# backend/models.py
from sqlalchemy import Column, Integer, String, Float, JSON, Boolean
from database import Base

class MatchPrediction(Base):
    # 💥 Renaming to v3 forces a fresh start with the new columns
    __tablename__ = "predictions_v3"

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
    
    # LIVE REALITY
    status = Column(String)        # "FT", "1H", "NS"
    minute = Column(Integer)       # 90
    actual_home_goals = Column(Integer, nullable=True)
    actual_away_goals = Column(Integer, nullable=True)
    
    # ✅ THE NEW FLAG (This caused the crash, now fixed!)
    is_settled = Column(Boolean, default=False)

    # THE GOLD MINE 🏆
    raw_data = Column(JSON, nullable=True)