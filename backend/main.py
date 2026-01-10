import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
from scipy.stats import poisson
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ IMPORT YOUR NEW MAPPING FILE
from mappings import NAME_MAP

app = FastAPI()

# --- CONFIG ---
ODDS_API_KEY = "9a605006b43a0074c7c7484f2978ed5b"
FOOTBALL_API_KEY = "7bea55228c0e0fbd7de71e7f5ff3802f"

# Limits & Caching
ODDS_CACHE_DURATION = 1800  # 30 mins
SCORES_CACHE_DURATION = 60  # 60 seconds

LEAGUE_CONFIG = { "Bundesliga": "soccer_germany_bundesliga" }
FOOTBALL_LEAGUE_ID = 78 
CURRENT_SEASON = 2024

# --- MEMORY ---
league_stats = {} 
api_cache = { 
    "odds": {"last_updated": 0, "data": []},
    "scores": {"last_updated": 0, "data": []} 
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: NAME NORMALIZER ---
def normalize_name(name):
    return name.lower().replace("fc ", "").replace(" 04", "").replace("sv ", "").replace("borussia ", "").replace(" 05", "").strip()

# --- 1. TRAINING LOGIC ---
def train_league_model(league_name):
    folder_path = os.path.join("data", league_name)
    if not os.path.exists(folder_path): 
        print(f"❌ Error: Data folder not found at {folder_path}")
        return None

    dfs = []
    print(f"📂 Loading data for {league_name}...")
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            try:
                dfs.append(pd.read_csv(os.path.join(folder_path, file)))
            except Exception as e: 
                print(f"  ⚠️ Failed to read {file}: {e}")
    
    if not dfs: 
        print("❌ No CSV files loaded!")
        return None
    
    full_df = pd.concat(dfs)
    df = full_df[full_df['Result'].notna()].copy()
    
    print(f"✅ Loaded {len(df)} historical matches for {league_name}")

    # Time Decay
    df['DateObj'] = pd.to_datetime(df['Date'], errors='coerce')
    latest = df['DateObj'].max()
    df['weight'] = np.exp(-0.0025 * (latest - df['DateObj']).dt.days)

    metric = 'xG' if 'xG' in df.columns else 'GF'
    game_map = df.set_index(['Date', 'Team'])[metric].to_dict()
    df['xGA'] = df.apply(lambda r: game_map.get((r['Date'], r['Opp']), 0), axis=1)

    h_games = df[df['Venue'] != '@']
    a_games = df[df['Venue'] == '@']
    avg_h = np.average(h_games[metric], weights=h_games['weight'])
    avg_a = np.average(a_games[metric], weights=a_games['weight'])

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

for league in LEAGUE_CONFIG:
    res = train_league_model(league)
    if res: league_stats[league] = res

# --- 2. MATH ENGINE ---
def calculate_all_probabilities(league, home, away):
    if league not in league_stats: return None
    db = league_stats[league]
    stats = db["stats"]
    
    # ✅ USE THE IMPORTED MAP
    home = NAME_MAP.get(home, home)
    away = NAME_MAP.get(away, away)

    # DEBUGGING: Print missing teams to Railway logs
    if home not in stats: print(f"⚠️ MISSING DATA: '{home}' (Not found in CSVs)")
    if away not in stats: print(f"⚠️ MISSING DATA: '{away}' (Not found in CSVs)")

    if home not in stats or away not in stats: return None

    h, a = stats[home], stats[away]
    xg_h = h['att_h'] * a['def_a'] * db['avg_h']
    xg_a = a['att_a'] * h['def_h'] * db['avg_a']

    prob_h, prob_d, prob_a = 0, 0, 0
    prob_o15, prob_o25 = 0, 0
    
    for i in range(10):
        for j in range(10):
            p = poisson.pmf(i, xg_h) * poisson.pmf(j, xg_a)
            if i > j: prob_h += p
            elif i == j: prob_d += p
            else: prob_a += p
            if (i+j) > 1.5: prob_o15 += p
            if (i+j) > 2.5: prob_o25 += p

    return {
        "1": prob_h, "X": prob_d, "2": prob_a,
        "1X": prob_h + prob_d, "X2": prob_d + prob_a,
        "O1.5": prob_o15, "U1.5": 1 - prob_o15,
        "O2.5": prob_o25, "U2.5": 1 - prob_o25
    }

# --- 3. LIVE SCORES FETCHER ---
def get_football_api_data():
    current_time = time.time()
    
    if current_time - api_cache["scores"]["last_updated"] < SCORES_CACHE_DURATION:
        return api_cache["scores"]["data"]
    
    today_str = date.today().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?league={FOOTBALL_LEAGUE_ID}&season={CURRENT_SEASON}&date={today_str}"
    
    headers = {
        "x-rapidapi-key": FOOTBALL_API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    try:
        res = requests.get(url, headers=headers).json()
        fixtures = res.get("response", [])
        
        simplified = []
        for f in fixtures:
            simplified.append({
                "home": f["teams"]["home"]["name"],
                "away": f["teams"]["away"]["name"],
                "status_short": f["fixture"]["status"]["short"], 
                "elapsed": f["fixture"]["status"]["elapsed"],
                "goals_h": f["goals"]["home"],
                "goals_a": f["goals"]["away"]
            })
            
        api_cache["scores"]["data"] = simplified
        api_cache["scores"]["last_updated"] = current_time
        return simplified
        
    except Exception as e:
        print(f"Football API Error: {e}")
        return []

# --- 4. MAIN ENDPOINT ---
@app.get("/live-edges")
def get_live_edges():
    current_time = time.time()
    
    odds_data = []
    if current_time - api_cache["odds"]["last_updated"] < ODDS_CACHE_DURATION and api_cache["odds"]["data"]:
        odds_data = api_cache["odds"]["data"]
    else:
        print("🔄 Fetching New Odds...")
        for league, key in LEAGUE_CONFIG.items():
            try:
                url = f"https://api.the-odds-api.com/v4/sports/{key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals&oddsFormat=decimal"
                res = requests.get(url).json()
                for game in res:
                    home, away = game['home_team'], game['away_team']
                    probs = calculate_all_probabilities(league, home, away)
                    
                    has_model = False
                    model_probs, fair_odds = {}, {}
                    if probs:
                        has_model = True
                        model_probs = {k: round(v * 100, 1) for k, v in probs.items()}
                        fair_odds = {k: round(1/v, 2) if v > 0 else 0 for k, v in probs.items()}

                    market_odds = { "1": 0, "X": 0, "2": 0, "O2.5": 0, "U2.5": 0 }
                    bookie = next((b for b in game['bookmakers'] if 'unibet' in b['key'] or 'betfair' in b['key']), game['bookmakers'][0] if game['bookmakers'] else None)
                    if bookie:
                        h2h = next((m for m in bookie['markets'] if m['key'] == 'h2h'), None)
                        if h2h:
                            for o in h2h['outcomes']:
                                if o['name'] == home: market_odds["1"] = o['price']
                                elif o['name'] == away: market_odds["2"] = o['price']
                                elif o['name'] == 'Draw': market_odds["X"] = o['price']
                        totals = next((m for m in bookie['markets'] if m['key'] == 'totals'), None)
                        if totals:
                            for o in totals['outcomes']:
                                if o.get('point') == 2.5:
                                    if o['name'] == 'Over': market_odds["O2.5"] = o['price']
                                    if o['name'] == 'Under': market_odds["U2.5"] = o['price']

                    odds_data.append({
                        "id": game['id'],
                        "date": game['commence_time'],
                        "match": f"{home} vs {away}",
                        "home_team": home, 
                        "away_team": away,
                        "league": league,
                        "has_model": has_model,
                        "probs": model_probs,
                        "fair_odds": fair_odds,
                        "market_odds": market_odds
                    })
                api_cache["odds"]["data"] = odds_data
                api_cache["odds"]["last_updated"] = current_time
            except Exception as e: print(f"Odds API Error: {e}")

    live_scores = get_football_api_data()
    
    final_results = []
    for game in odds_data:
        game["score"] = None
        h_norm = normalize_name(game["home_team"])
        
        for score in live_scores:
            if h_norm in normalize_name(score["home"]):
                game["score"] = {
                    "status": score["status_short"], 
                    "time": score["elapsed"],
                    "goals_h": score["goals_h"],
                    "goals_a": score["goals_a"]
                }
                break
        
        final_results.append(game)

    final_results.sort(key=lambda x: x['date'])
    return final_results