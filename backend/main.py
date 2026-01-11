import os
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
from scipy.stats import poisson
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# ✅ Import Database tools
from database import engine, get_db, Base
from models import MatchPrediction
from mappings import NAME_MAP

# Update Tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CONFIG ---
FOOTBALL_API_KEY = "7bea55228c0e0fbd7de71e7f5ff3802f"
LEAGUE_CONFIG = { "Bundesliga": 78 } 
CURRENT_SEASON = 2025 
CACHE_DURATION = 60 

api_cache = { "last_updated": 0, "data": [] }
league_stats = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def normalize_name(name):
    return name.lower().replace("fc ", "").replace(" 04", "").replace("sv ", "").replace("borussia ", "").replace(" 05", "").replace("1. ", "").strip()

# --- 1. TRAINING ---
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
    
    df['DateObj'] = pd.to_datetime(df['Date'], errors='coerce')
    latest = df['DateObj'].max()
    df['weight'] = np.exp(-0.0025 * (latest - df['DateObj']).dt.days)

    metric = 'xG' if 'xG' in df.columns else 'GF'
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
    
    print(f"✅ LOADED TEAMS: {len(stats)}")
    return {"stats": stats, "avg_h": avg_h, "avg_a": avg_a}

train_res = train_league_model("Bundesliga")
if train_res: league_stats["Bundesliga"] = train_res

# --- 2. MATH ---
def calculate_all_probabilities(league, home, away):
    if league not in league_stats: return None
    db_stats = league_stats[league]
    stats = db_stats["stats"]
    
    home_mapped = NAME_MAP.get(home, home)
    away_mapped = NAME_MAP.get(away, away)

    if home_mapped not in stats:
        for k in stats.keys():
            if normalize_name(home) == normalize_name(k):
                home_mapped = k
                break
    if away_mapped not in stats:
        for k in stats.keys():
            if normalize_name(away) == normalize_name(k):
                away_mapped = k
                break

    if home_mapped not in stats or away_mapped not in stats: return None

    h, a = stats[home_mapped], stats[away_mapped]
    xg_h = h['att_h'] * a['def_a'] * db_stats['avg_h']
    xg_a = a['att_a'] * h['def_h'] * db_stats['avg_a']

    prob_h, prob_d, prob_a = 0, 0, 0
    for i in range(10):
        for j in range(10):
            p = poisson.pmf(i, xg_h) * poisson.pmf(j, xg_a)
            if i > j: prob_h += p
            elif i == j: prob_d += p
            else: prob_a += p

    return {"1": prob_h, "X": prob_d, "2": prob_a, "1X": prob_h + prob_d, "X2": prob_d + prob_a, "xg_h": xg_h, "xg_a": xg_a}

# --- 3. THE SETTLEMENT ENGINE 🏆 ---
def settle_finished_games(db: Session):
    # Find 1 game that is finished (FT) but NOT settled
    game_to_settle = db.query(MatchPrediction).filter(
        MatchPrediction.status == "FT",
        MatchPrediction.is_settled == False
    ).first()

    if not game_to_settle:
        return # Nothing to do

    print(f"⛏️ Mining Gold Data for: {game_to_settle.home_team} vs {game_to_settle.away_team}...")
    
    headers = {
        "x-rapidapi-key": FOOTBALL_API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }
    
    fix_id = game_to_settle.fixture_id
    gold_data = game_to_settle.raw_data or {}

    try:
        # 1. Fetch Statistics (xG, Shots, Corners)
        stats_res = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fix_id}", headers=headers).json()
        gold_data["statistics"] = stats_res.get("response", [])

        # 2. Fetch Events (Goals, Cards, Subs)
        events_res = requests.get(f"https://v3.football.api-sports.io/fixtures/events?fixture={fix_id}", headers=headers).json()
        gold_data["events"] = events_res.get("response", [])

        # 3. Fetch Lineups (Players)
        lineups_res = requests.get(f"https://v3.football.api-sports.io/fixtures/lineups?fixture={fix_id}", headers=headers).json()
        gold_data["lineups"] = lineups_res.get("response", [])

        # ✅ Save & Mark Settled
        game_to_settle.raw_data = gold_data
        game_to_settle.is_settled = True
        db.commit()
        print(f"✅ Data Captured & Settled!")

    except Exception as e:
        print(f"❌ Settlement Failed: {e}")

# --- 4. MAIN ENDPOINT ---
@app.get("/live-edges")
def get_live_edges(db: Session = Depends(get_db)):
    # ⛏️ Run the miner first (Opportunistic Settlement)
    settle_finished_games(db)

    current_time = time.time()
    
    if current_time - api_cache["last_updated"] < CACHE_DURATION and api_cache["data"]:
        return api_cache["data"]

    print(f"🚀 Fetching Live & Upcoming Data...")
    headers = {
        "x-rapidapi-key": FOOTBALL_API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io"
    }

    combined_fixtures = []
    seen_ids = set()

    # Fetch Live & Next
    for endpoint in ["live=all", "next=30"]:
        try:
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?league=78&season={CURRENT_SEASON}&{endpoint}", headers=headers)
            if res.status_code == 200:
                games = res.json().get("response", [])
                for g in games:
                    if g["fixture"]["id"] not in seen_ids:
                        combined_fixtures.append(g)
                        seen_ids.add(g["fixture"]["id"])
        except: pass

    final_results = []
    
    for f in combined_fixtures:
        try:
            fix_id = f["fixture"]["id"]
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            
            probs = calculate_all_probabilities("Bundesliga", home, away)
            
            has_model = False
            model_probs, fair_odds, predicted_score = {}, {}, None
            
            if probs:
                has_model = True
                model_probs = {k: round(v * 100, 1) for k, v in probs.items() if k in ["1","X","2","1X","X2"]}
                fair_odds = {k: round(1/v, 2) if v > 0 else 0 for k, v in probs.items() if k in ["1","X","2","1X","X2"]}
                predicted_score = f"{probs['xg_h']:.2f} - {probs['xg_a']:.2f}"

                # 💾 DATABASE SYNC
                existing = db.query(MatchPrediction).filter(MatchPrediction.fixture_id == fix_id).first()
                
                status = f["fixture"]["status"]["short"]
                
                if not existing:
                    new_rec = MatchPrediction(
                        fixture_id=fix_id, home_team=home, away_team=away, league="Bundesliga",
                        match_date=f["fixture"]["date"],
                        model_home_xg=float(probs['xg_h']), model_away_xg=float(probs['xg_a']),
                        fair_odd_home=float(fair_odds.get("1", 0)), fair_odd_draw=float(fair_odds.get("X", 0)), fair_odd_away=float(fair_odds.get("2", 0)),
                        status=status, minute=f["fixture"]["status"]["elapsed"],
                        actual_home_goals=f["goals"]["home"], actual_away_goals=f["goals"]["away"],
                        raw_data=f # Initial raw data (basic)
                    )
                    db.add(new_rec)
                    db.commit()
                else:
                    # Update Live Status
                    existing.status = status
                    existing.minute = f["fixture"]["status"]["elapsed"]
                    existing.actual_home_goals = f["goals"]["home"]
                    existing.actual_away_goals = f["goals"]["away"]
                    # Don't overwrite raw_data if we already mined gold (settled)
                    if not existing.is_settled:
                        existing.raw_data = f
                    db.commit()

            # Odds
            market_odds = { "1": 0, "X": 0, "2": 0, "1X": 0, "X2": 0 }
            res_odds = requests.get(f"https://v3.football.api-sports.io/odds?fixture={fix_id}", headers=headers).json()
            if res_odds.get("response"):
                bookies = res_odds["response"][0]["bookmakers"]
                bookie = next((b for b in bookies if b["id"] == 1), bookies[0] if bookies else None)
                if bookie:
                    for bet in bookie["bets"]:
                        if bet["id"] == 1:
                             for v in bet["values"]:
                                if v["value"] == "Home": market_odds["1"] = float(v["odd"])
                                if v["value"] == "Away": market_odds["2"] = float(v["odd"])
                                if v["value"] == "Draw": market_odds["X"] = float(v["odd"])
                        if bet["id"] == 12:
                             for v in bet["values"]:
                                if v["value"] == "Home/Draw": market_odds["1X"] = float(v["odd"])
                                if v["value"] == "Draw/Away": market_odds["X2"] = float(v["odd"])

            final_results.append({
                "id": fix_id,
                "date": f["fixture"]["date"],
                "match": f"{home} vs {away}",
                "home_team": home,
                "away_team": away,
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
                "predicted_xg": predicted_score,
                "market_odds": market_odds
            })
        except Exception as e: print(f"❌ Error {f.get('fixture',{}).get('id')}: {e}")

    final_results.sort(key=lambda x: x['date'])
    api_cache["data"] = final_results
    api_cache["last_updated"] = current_time
    return final_results