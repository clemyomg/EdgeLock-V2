import os
import time
import requests
import pandas as pd
import numpy as np
from scipy.stats import poisson
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# --- CONFIG ---
ODDS_API_KEY = "9a605006b43a0074c7c7484f2978ed5b"
CACHE_DURATION = 1800 # 30 mins
LEAGUE_CONFIG = { "Bundesliga": "soccer_germany_bundesliga" }

# --- MEMORY ---
league_stats = {} 
api_cache = { "last_updated": 0, "data": [] }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TRAINING LOGIC ---
def train_league_model(league_name):
    folder_path = os.path.join("data", league_name)
    if not os.path.exists(folder_path): return None

    dfs = []
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            try:
                dfs.append(pd.read_csv(os.path.join(folder_path, file)))
            except: pass
    
    if not dfs: return None
    
    full_df = pd.concat(dfs)
    df = full_df[full_df['Result'].notna()].copy()
    
    # Time Decay
    df['DateObj'] = pd.to_datetime(df['Date'], errors='coerce')
    latest = df['DateObj'].max()
    df['weight'] = np.exp(-0.0025 * (latest - df['DateObj']).dt.days)

    # Metric & Defense
    metric = 'xG' if 'xG' in df.columns else 'GF'
    game_map = df.set_index(['Date', 'Team'])[metric].to_dict()
    df['xGA'] = df.apply(lambda r: game_map.get((r['Date'], r['Opp']), 0), axis=1)

    # Averages
    h_games = df[df['Venue'] != '@']
    a_games = df[df['Venue'] == '@']
    avg_h = np.average(h_games[metric], weights=h_games['weight'])
    avg_a = np.average(a_games[metric], weights=a_games['weight'])

    # Ratings
    stats = {}
    for team in df['Team'].unique():
        th = h_games[h_games['Team'] == team]
        ta = a_games[a_games['Team'] == team]
        if len(th) > 2:
            stats[team] = {
                'att_h': np.average(th[metric], weights=th['weight']) / avg_h,
                'def_h': np.average(th['xGA'], weights=th['weight']) / avg_a,
                'att_a': np.average(ta[metric], weights=ta['weight']) / avg_a,
                'def_a': np.average(ta['xGA'], weights=ta['weight']) / avg_h
            }
            
    return {"stats": stats, "avg_h": avg_h, "avg_a": avg_a}

# Train on Startup
for league in LEAGUE_CONFIG:
    res = train_league_model(league)
    if res: league_stats[league] = res

# --- MATH ENGINE ---
def calculate_all_probabilities(league, home, away):
    if league not in league_stats: return None
    db = league_stats[league]
    stats = db["stats"]
    
    # Name Mapping
    name_map = {
        "Eintracht Frankfurt": "Eint Frankfurt", "Köln": "1. FC Köln", 
        "Bayer Leverkusen": "Leverkusen", "Borussia Mönchengladbach": "M'gladbach",
        "Hamburger SV": "Hamburger SV"
    }
    home = name_map.get(home, home)
    away = name_map.get(away, away)

    if home not in stats or away not in stats: return None

    h, a = stats[home], stats[away]
    xg_h = h['att_h'] * a['def_a'] * db['avg_h']
    xg_a = a['att_a'] * h['def_h'] * db['avg_a']

    # Full Matrix Simulation
    prob_h, prob_d, prob_a = 0, 0, 0
    prob_o15, prob_o25 = 0, 0
    
    for i in range(10):
        for j in range(10):
            p = poisson.pmf(i, xg_h) * poisson.pmf(j, xg_a)
            
            # 1X2
            if i > j: prob_h += p
            elif i == j: prob_d += p
            else: prob_a += p
            
            # Goals
            total_goals = i + j
            if total_goals > 1.5: prob_o15 += p
            if total_goals > 2.5: prob_o25 += p

    return {
        "1": prob_h,
        "X": prob_d,
        "2": prob_a,
        "1X": prob_h + prob_d,
        "X2": prob_d + prob_a,
        "O1.5": prob_o15,
        "U1.5": 1 - prob_o15,
        "O2.5": prob_o25,
        "U2.5": 1 - prob_o25
    }

@app.get("/live-edges")
def get_live_edges():
    current_time = time.time()
    
    # Cache Check
    if current_time - api_cache["last_updated"] < CACHE_DURATION and api_cache["data"]:
        return api_cache["data"]

    print("🔄 Fetching New Odds...")
    all_results = []
    
    for league, key in LEAGUE_CONFIG.items():
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
            res = requests.get(url).json()
            
            for game in res:
                home, away = game['home_team'], game['away_team']
                commence_time = game['commence_time'] # NEW: Get Date

                probs = calculate_all_probabilities(league, home, away)
                if not probs: continue
                
                market_odds = { "1": 0, "X": 0, "2": 0, "O2.5": 0, "U2.5": 0 }

                # Parse Bookie Odds
                bookie = next((b for b in game['bookmakers'] if 'unibet' in b['key'] or 'betfair' in b['key']), game['bookmakers'][0] if game['bookmakers'] else None)
                if bookie:
                    # H2H
                    h2h = next((m for m in bookie['markets'] if m['key'] == 'h2h'), None)
                    if h2h:
                        for o in h2h['outcomes']:
                            if o['name'] == home: market_odds["1"] = o['price']
                            elif o['name'] == away: market_odds["2"] = o['price']
                            elif o['name'] == 'Draw': market_odds["X"] = o['price']
                    
                    # Totals
                    totals = next((m for m in bookie['markets'] if m['key'] == 'totals'), None)
                    if totals:
                        for o in totals['outcomes']:
                            if o.get('point') == 2.5:
                                if o['name'] == 'Over': market_odds["O2.5"] = o['price']
                                if o['name'] == 'Under': market_odds["U2.5"] = o['price']

                all_results.append({
                    "id": game['id'],
                    "date": commence_time, # NEW: Sending date to frontend
                    "match": f"{home} vs {away}",
                    "league": league,
                    "bookie": bookie['title'] if bookie else "Unknown",
                    "probs": {k: round(v * 100, 1) for k, v in probs.items()},
                    "fair_odds": {k: round(1/v, 2) if v > 0 else 0 for k, v in probs.items()},
                    "market_odds": market_odds
                })

        except Exception as e:
            print(f"Error {league}: {e}")

    # NEW: Sort by Date (Earliest first)
    all_results.sort(key=lambda x: x['date'])

    api_cache["data"] = all_results
    api_cache["last_updated"] = current_time
    return all_results