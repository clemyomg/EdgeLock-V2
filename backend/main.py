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
from sqlalchemy import desc, or_
from sqlalchemy.exc import OperationalError

from database import engine, get_db, Base
from models import MatchPrediction
from mappings import NAME_MAP

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- CONFIG ---
FOOTBALL_API_KEY = "7bea55228c0e0fbd7de71e7f5ff3802f"
LEAGUE_CONFIG = { "Bundesliga": 78, "Premier League": 39, "La Liga": 140, "Serie A": 135, "Ligue 1": 61 } 
CURRENT_SEASON = 2025 
CACHE_DURATION = 300 

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
            try: dfs.append(pd.read_csv(os.path.join(folder_path, file)))
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
            if normalize_name(home) == normalize_name(k): home_mapped = k; break
    if away_mapped not in stats:
        for k in stats.keys():
            if normalize_name(away) == normalize_name(k): away_mapped = k; break
    if home_mapped not in stats or away_mapped not in stats: return None
    h, a = stats[home_mapped], stats[away_mapped]
    xg_h = h['att_h'] * a['def_a'] * db_stats['avg_h']
    xg_a = a['att_a'] * h['def_h'] * db_stats['avg_a']
    prob_h, prob_d, prob_a = 0, 0, 0
    
    # Goals 1.5 - 4.5
    goal_keys = [1.5, 2.5, 3.5, 4.5]
    probs_goals = {f"Over{x}": 0 for x in goal_keys}
    
    # Full Range of Handicaps
    handicap_lines = [-2.5, -2.0, -1.5, -1.0, -0.5, 0.5, 1.0, 1.5, 2.0, 2.5]
    probs_handicap = {f"Home{'+' if h>0 else ''}{h}": 0 for h in handicap_lines}

    max_score_prob = 0
    most_likely_score = (0, 0)

    for i in range(15): 
        for j in range(15):
            p = poisson.pmf(i, xg_h) * poisson.pmf(j, xg_a)
            if p > max_score_prob:
                max_score_prob = p
                most_likely_score = (i, j)
            if i > j: prob_h += p
            elif i == j: prob_d += p
            else: prob_a += p
            
            total = i + j
            for x in goal_keys:
                if total > x: probs_goals[f"Over{x}"] += p

            for h in handicap_lines:
                if (i + h) > j: probs_handicap[f"Home{'+' if h>0 else ''}{h}"] += p

    result = { 
        "1": prob_h, "X": prob_d, "2": prob_a, "1X": prob_h + prob_d, "X2": prob_d + prob_a,
        "xg_h": xg_h, "xg_a": xg_a, "most_likely_score": f"{most_likely_score[0]}-{most_likely_score[1]}"
    }
    for k, v in probs_goals.items():
        result[k] = v
        result[k.replace("Over", "Under")] = 1 - v
    for h in handicap_lines:
        key = f"Home{'+' if h>0 else ''}{h}"
        result[key] = probs_handicap[key]
        result[f"Away{'+' if -h>0 else ''}{-h}"] = 1 - probs_handicap[key]

    return result

# --- 3. SETTLEMENT ---
def settle_finished_games(db: Session):
    try:
        game = db.query(MatchPrediction).filter(MatchPrediction.status == "FT", MatchPrediction.is_settled == False).first()
        if not game: return 
        headers = { "x-rapidapi-key": FOOTBALL_API_KEY, "x-rapidapi-host": "v3.football.api-sports.io" }
        stats = requests.get(f"https://v3.football.api-sports.io/fixtures/statistics?fixture={game.fixture_id}", headers=headers).json().get("response", [])
        game.is_settled = True
        current_raw = game.raw_data or {}
        current_raw["statistics"] = stats
        game.raw_data = current_raw
        db.commit()
    except Exception as e: 
        print(f"Settlement Error: {e}")
        db.rollback()

# --- 4. MAIN ENDPOINT ---
@app.get("/live-edges")
def get_live_edges(db: Session = Depends(get_db)):
    settle_finished_games(db)
    current_time = time.time()
    
    history = []
    try:
        settled = db.query(MatchPrediction).filter(MatchPrediction.status == "FT").order_by(desc(MatchPrediction.id)).limit(20).all()
        for g in settled:
            history.append({
                "match": f"{g.home_team} vs {g.away_team}",
                "score": f"{g.actual_home_goals}-{g.actual_away_goals}",
                "prediction": f"{g.model_home_xg:.2f} - {g.model_away_xg:.2f}",
                "result": "Settled"
            })
    except OperationalError:
        db.rollback()
        history = []

    if current_time - api_cache["last_updated"] < CACHE_DURATION and api_cache["data"]: 
        return { "matches": api_cache["data"], "history": history }

    headers = { "x-rapidapi-key": FOOTBALL_API_KEY, "x-rapidapi-host": "v3.football.api-sports.io" }
    combined_fixtures = []
    
    # 1. FETCH FIXTURES
    print("📡 Fetching Fixtures for Bundesliga...")
    for league_name, league_id in LEAGUE_CONFIG.items():
        if league_name not in league_stats: continue
        try:
            res = requests.get(f"https://v3.football.api-sports.io/fixtures?league={league_id}&season={CURRENT_SEASON}&next=10", headers=headers)
            if res.status_code == 200:
                games = res.json().get("response", [])
                if games: combined_fixtures.extend(games)
        except: pass
    
    print(f"✅ Found {len(combined_fixtures)} games for Bundesliga")

    # 2. DEEP SCAN (No Bulk)
    odds_cache = {} 

    # DB FALLBACK
    if not combined_fixtures:
        print("⚠️ API Limit? Using DB.")
        db_games = db.query(MatchPrediction).filter(or_(MatchPrediction.status != "FT", MatchPrediction.is_settled == False)).all()
        fallback_results = []
        for g in db_games:
            probs = calculate_all_probabilities(g.league, g.home_team, g.away_team)
            if not probs: continue
            row = {
                "id": g.fixture_id, "date": g.match_date, "match": f"{g.home_team} vs {g.away_team}",
                "home_team": g.home_team, "away_team": g.away_team, "league": g.league,
                "league_logo": g.raw_data.get("league",{}).get("logo"), "country_flag": g.raw_data.get("league",{}).get("flag"),
                "home_logo": g.raw_data.get("teams",{}).get("home",{}).get("logo"), "away_logo": g.raw_data.get("teams",{}).get("away",{}).get("logo"),
                "score": { "status": g.status, "time": g.minute, "goals_h": g.actual_home_goals, "goals_a": g.actual_away_goals },
                "has_model": True,
                "probs": {k: round(v * 100, 1) for k, v in probs.items() if k not in ["xg_h", "xg_a", "most_likely_score"]},
                "predicted_xg": { "home": f"{probs['xg_h']:.2f}", "away": f"{probs['xg_a']:.2f}" },
                "most_likely_score": probs["most_likely_score"],
                "market_odds": g.raw_data.get("market_odds_cache", {})
            }
            fallback_results.append(row)
        fallback_results.sort(key=lambda x: x['date'])
        return { "matches": fallback_results, "history": history }

    seen_ids = set()
    final_results = []
    
    print("📡 Fetching Deep Odds for Bundesliga...")

    for f in combined_fixtures:
        if f["fixture"]["id"] in seen_ids: continue
        seen_ids.add(f["fixture"]["id"])
        
        has_model = False 
        
        try:
            fix_id = f["fixture"]["id"]
            home, away = f["teams"]["home"]["name"], f["teams"]["away"]["name"]
            league_name = f["league"]["name"]
            if league_name == "Bundesliga 1": league_name = "Bundesliga"

            probs = calculate_all_probabilities(league_name, home, away)
            if not probs: continue 

            has_model = True
            model_probs = {k: round(v * 100, 1) for k, v in probs.items() if k not in ["xg_h", "xg_a", "most_likely_score"]}
            score_display = probs["most_likely_score"]
            predicted_score = { "home": f"{probs['xg_h']:.2f}", "away": f"{probs['xg_a']:.2f}" }
            
            # --- MARKET PARSER ---
            market_odds = { "1": 0, "X": 0, "2": 0, "1X": 0, "X2": 0, "Handicaps": [], "Goals": {} }
            for g_line in [1.5, 2.5, 3.5, 4.5]:
                market_odds["Goals"][f"{g_line}"] = { "Over": 0, "Under": 0 }

            # FORCE DEEP FETCH
            print(f"🔍 Deep Fetch for Match {fix_id}...")
            bookies = []
            try:
                res_odds = requests.get(f"https://v3.football.api-sports.io/odds?fixture={fix_id}", headers=headers).json()
                bookies = res_odds.get("response", [])[0].get("bookmakers", [])
            except: pass

            if bookies:
                preferred = [1, 8, 3] 
                bookies.sort(key=lambda b: preferred.index(b["id"]) if b["id"] in preferred else 999)
                
                found_bets = set()

                for bookie in bookies:
                    for bet in bookie["bets"]:
                        
                        # Bet 6: Standard Goals
                        if bet["id"] == 6:
                            for v in bet["values"]:
                                val_str = str(v["value"]) 
                                odd_val = float(v["odd"])
                                for g_line in [1.5, 2.5, 3.5, 4.5]:
                                    if val_str == f"Over {g_line}" and market_odds["Goals"][str(g_line)]["Over"] == 0:
                                        market_odds["Goals"][str(g_line)]["Over"] = odd_val
                                    if val_str == f"Under {g_line}" and market_odds["Goals"][str(g_line)]["Under"] == 0:
                                        market_odds["Goals"][str(g_line)]["Under"] = odd_val

                        # Bet 1: Winner
                        elif bet["id"] == 1 and "winner" not in found_bets:
                            for v in bet["values"]:
                                if v["value"] == "Home": market_odds["1"] = float(v["odd"])
                                if v["value"] == "Away": market_odds["2"] = float(v["odd"])
                                if v["value"] == "Draw": market_odds["X"] = float(v["odd"])
                            if market_odds["1"] > 0: found_bets.add("winner")

                        # Bet 12: DC
                        elif bet["id"] == 12 and "dc" not in found_bets:
                            for v in bet["values"]:
                                if v["value"] == "Home/Draw": market_odds["1X"] = float(v["odd"])
                                if v["value"] == "Draw/Away": market_odds["X2"] = float(v["odd"])
                            if market_odds["1X"] > 0: found_bets.add("dc")

                        # Bet 5 (Asian) OR Bet 4 (Alt Asian)
                        elif bet["id"] in [5, 4]:
                            for v in bet["values"]:
                                try:
                                    label = str(v["value"]) 
                                    odd = float(v["odd"])
                                    
                                    # 1. Asian Goal Line
                                    if "Over" in label or "Under" in label:
                                        parts = label.split(" ")
                                        if len(parts) >= 2:
                                            line_val = parts[1]
                                            type_val = parts[0]
                                            if line_val in market_odds["Goals"]:
                                                market_odds["Goals"][line_val][type_val] = odd
                                                print(f"✅ Found Goal Odd: {type_val} {line_val} -> {odd}")
                                        continue 

                                    # 2. Team Handicap (+1.5, +2.5) with SAFETY FILTER
                                    if "1.5" in label or "2.5" in label:
                                        # SAFETY FILTER: Only accept odds < 2.5 (High probability / Safety bets)
                                        if odd < 2.5:
                                            # SMART FIX: If odd is Safe (< 2.5), assume Positive Handicap (+)
                                            # This fixes the API's inverted sign issue (e.g. "Away -1.5" -> "Away +1.5")
                                            clean_label = label.replace("-", "+")
                                            
                                            if not any(h["label"] == clean_label for h in market_odds["Handicaps"]):
                                                market_odds["Handicaps"].append({ "label": clean_label, "odd": odd })
                                                print(f"✅ Found Safe Handicap (Fixed): {clean_label} -> {odd}")
                                        
                                except: pass

            f["market_odds_cache"] = market_odds 
            existing = db.query(MatchPrediction).filter(MatchPrediction.fixture_id == fix_id).first()
            if not existing:
                db.add(MatchPrediction(fixture_id=fix_id, home_team=home, away_team=away, league=league_name, match_date=f["fixture"]["date"],
                    model_home_xg=float(probs['xg_h']) if probs else 0, model_away_xg=float(probs['xg_a']) if probs else 0,
                    status=f["fixture"]["status"]["short"], minute=f["fixture"]["status"]["elapsed"], raw_data=f))
                db.commit()
            else:
                existing.raw_data = f
                db.commit()

            final_results.append({
                "id": fix_id, "date": f["fixture"]["date"], "match": f"{home} vs {away}", "home_team": home, "away_team": away,
                "league": league_name, "league_logo": f["league"]["logo"], "country_flag": f["league"]["flag"], 
                "home_logo": f["teams"]["home"]["logo"], "away_logo": f["teams"]["away"]["logo"], "round": f["league"]["round"],
                "score": { "status": f["fixture"]["status"]["short"], "time": f["fixture"]["status"]["elapsed"], "goals_h": f["goals"]["home"], "goals_a": f["goals"]["away"] },
                "has_model": has_model, "probs": model_probs, "predicted_xg": predicted_score, 
                "most_likely_score": score_display,
                "market_odds": market_odds,
                "events": f.get("events", [])
            })
        except Exception as e: print(f"❌ Error processing match: {e}")

    final_results.sort(key=lambda x: x['date'])
    api_cache["data"] = final_results
    api_cache["last_updated"] = current_time
    return { "matches": final_results, "history": history }