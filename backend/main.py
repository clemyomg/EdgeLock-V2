import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
from scipy.stats import poisson
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ Import your map
from mappings import NAME_MAP

app = FastAPI()

# --- CONFIG ---
FOOTBALL_API_KEY = "7bea55228c0e0fbd7de71e7f5ff3802f"
LEAGUE_CONFIG = { "Bundesliga": 78 } 
CURRENT_SEASON = 2025 # 2025-2026 Season

# Caching (10 mins)
CACHE_DURATION = 600 

# --- MEMORY ---
league_stats = {} 
api_cache = { "last_updated": 0, "data": [] }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HELPER: NAME NORMALIZER ---
def normalize_name(name):
    # Removes common prefixes/suffixes to help matching
    return name.lower().replace("fc ", "").replace(" 04", "").replace("sv ", "").replace("borussia ", "").replace(" 05", "").replace("1. ", "").strip()

# --- 1. TRAINING LOGIC (With Debugging) ---
def train_league_model(league_name):
    folder_path = os.path.join("data", league_name)
    if not os.path.exists(folder_path): 
        print(f"⚠️ Error: Folder not found {folder_path}")
        return None

    dfs = []
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            try:
                dfs.append(pd.read_csv(os.path.join(folder_path, file)))
            except: pass
    
    if not dfs: return None
    
    full_df = pd.concat(dfs)
    df = full_df[full_df['Result'].notna()].copy()
    
    df['DateObj'] = pd.to_datetime(df['Date'], errors='coerce')
    latest = df['DateObj'].max()
    df['weight'] = np.exp(-0.0025 * (latest - df['DateObj']).dt.days)

    metric = 'xG' if 'xG' in df.columns else 'GF'
    # Fallback if xG is missing
    if metric not in df.columns: metric = 'GF'

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
            
    print(f"✅ LOADED TEAMS FOR {league_name}: {list(stats.keys())}") # 👈 THIS WILL SHOW IN LOGS
    return {"stats": stats, "avg_h": avg_h, "avg_a": avg_a}

# Train on Startup
train_res = train_league_model("Bundesliga")
if train_res: league_stats["Bundesliga"] = train_res

# --- 2. SMART MATCHING ENGINE ---
def find_best_match_key(target_name, stats_keys):
    # 1. Exact Match
    if target_name in stats_keys: return target_name
    
    # 2. Mapped Match
    mapped = NAME_MAP.get(target_name)
    if mapped and mapped in stats_keys: return mapped

    # 3. Normalized Fuzzy Match
    norm_target = normalize_name(target_name)
    for k in stats_keys:
        norm_k = normalize_name(k)
        # Check if one contains the other (e.g. "Bayern" in "Bayern Munchen")
        if norm_target in norm_k or norm_k in norm_target:
            return k
            
    return None

def calculate_all_probabilities(league, home, away):
    if league not in league_stats: return None
    db = league_stats[league]
    stats = db["stats"]
    
    # Use Smart Matcher
    home_key = find_best_match_key(home, stats.keys())
    away_key = find_best_match_key(away, stats.keys())

    if not home_key or not away_key:
        print(f"❌ FAILED MATCH: {home} (Found: {home_key}) vs {away} (Found: {away_key})")
        return None

    h, a = stats[home_key], stats[away_key]
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

# --- 3. API-FOOTBALL ENGINE ---
@app.get("/live-edges")
def get_live_edges():
    current_time = time.time()
    
    if current_time - api_cache["last_updated"] < CACHE_DURATION and api_cache["data"]:
        return api_cache["data"]

    print(f"🚀 Fetching Data (Season {CURRENT_SEASON})...")
    final_results = []
    
    headers = {
        "x-rapidapi-key": FOOTBALL_API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }

    url_fixtures = f"https://v3.football.api-sports.io/fixtures?league=78&season={CURRENT_SEASON}&next=30"
    
    try:
        res_fix = requests.get(url_fixtures, headers=headers)
        if res_fix.status_code != 200: 
            print(f"API Error: {res_fix.text}")
            return []

        fixtures = res_fix.json().get("response", [])
        
        for f in fixtures:
            fix_id = f["fixture"]["id"]
            home_name = f["teams"]["home"]["name"]
            away_name = f["teams"]["away"]["name"]
            
            # MODEL
            probs = calculate_all_probabilities("Bundesliga", home_name, away_name)
            
            has_model = False
            model_probs, fair_odds = {}, {}
            if probs:
                has_model = True
                model_probs = {k: round(v * 100, 1) for k, v in probs.items()}
                fair_odds = {k: round(1/v, 2) if v > 0 else 0 for k, v in probs.items()}

            # ODDS
            market_odds = { "1": 0, "X": 0, "2": 0, "1X": 0, "X2": 0, "H_Spread": 0, "H_Spread_Point": 0, "A_Spread": 0, "A_Spread_Point": 0 }
            
            url_odds = f"https://v3.football.api-sports.io/odds?fixture={fix_id}"
            res_odds = requests.get(url_odds, headers=headers).json()
            
            if res_odds.get("response"):
                all_bookies = res_odds["response"][0]["bookmakers"]
                for bookie in all_bookies:
                    if market_odds["1"] > 0 and market_odds["1X"] > 0: break 
                    
                    for bet in bookie["bets"]:
                        if bet["id"] == 1 and market_odds["1"] == 0:
                            for v in bet["values"]:
                                if v["value"] == "Home": market_odds["1"] = float(v["odd"])
                                if v["value"] == "Away": market_odds["2"] = float(v["odd"])
                                if v["value"] == "Draw": market_odds["X"] = float(v["odd"])
                        
                        if bet["id"] == 12 and market_odds["1X"] == 0:
                            for v in bet["values"]:
                                if v["value"] == "Home/Draw": market_odds["1X"] = float(v["odd"])
                                if v["value"] == "Draw/Away": market_odds["X2"] = float(v["odd"])

            final_results.append({
                "id": fix_id,
                "date": f["fixture"]["date"],
                "match": f"{home_name} vs {away_name}",
                "home_team": home_name, 
                "away_team": away_name,
                "league": "Bundesliga",
                "round": f["league"]["round"],
                "score": {
                    "status": f["fixture"]["status"]["short"],
                    "time": f["fixture"]["status"]["elapsed"],
                    "goals_h": f["goals"]["home"],
                    "goals_a": f["goals"]["away"]
                },
                "has_model": has_model, 
                "probs": model_probs,
                "fair_odds": fair_odds,
                "market_odds": market_odds
            })

    except Exception as e:
        print(f"❌ Error: {e}")

    final_results.sort(key=lambda x: x['date'])
    api_cache["data"] = final_results
    api_cache["last_updated"] = current_time
    return final_results