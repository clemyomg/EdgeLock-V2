# backend/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base

class MatchPrediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, unique=True, index=True) # API-Football ID
    
    # Match Details
    home_team = Column(String)
    away_team = Column(String)
    league = Column(String)
    match_date = Column(String)
    
    # YOUR BRAIN (The "Book")
    model_home_xg = Column(Float) # Your calculated xG
    model_away_xg = Column(Float)
    fair_odd_home = Column(Float)
    fair_odd_away = Column(Float)
    fair_odd_draw = Column(Float)
    
    # REALITY (Filled later)
    actual_home_goals = Column(Integer, nullable=True)
    actual_away_goals = Column(Integer, nullable=True)
    actual_home_xg = Column(Float, nullable=True) # From API-Football stats
    actual_away_xg = Column(Float, nullable=True)