# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from database import Base

class MatchPrediction(Base):
    # 💥 Renaming this forces Railway to build a NEW table with all columns
    __tablename__ = "predictions_v2"

    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, unique=True, index=True) 
    
    # Match Info
    home_team = Column(String)
    away_team = Column(String)
    league = Column(String)
    match_date = Column(String)
    
    # YOUR BRAIN (The "Book")
    model_home_xg = Column(Float)
    model_away_xg = Column(Float)
    fair_odd_home = Column(Float)
    fair_odd_draw = Column(Float)
    fair_odd_away = Column(Float)
    
    # LIVE REALITY (Updated in real-time)
    status = Column(String)        # e.g., "FT", "1H"
    minute = Column(Integer)       # e.g., 60
    actual_home_goals = Column(Integer, nullable=True)
    actual_away_goals = Column(Integer, nullable=True)
    
    # THE GOLD MINE 🏆
    # Stores EVERYTHING: Events, Cards, Weather, Lineups
    raw_data = Column(JSON, nullable=True)