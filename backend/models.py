from sqlalchemy import Column, Integer, String, Float, JSON, Boolean
from database import Base

class MatchPrediction(Base):
    __tablename__ = "predictions_v4" # 💥 New Table

    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, unique=True, index=True) 
    
    # Match Info
    home_team = Column(String)
    away_team = Column(String)
    league = Column(String)
    match_date = Column(String)
    
    # YOUR BRAIN
    model_home_xg = Column(Float)
    model_away_xg = Column(Float)
    fair_odd_home = Column(Float)
    fair_odd_draw = Column(Float)
    fair_odd_away = Column(Float)
    
    # LIVE REALITY
    status = Column(String)
    minute = Column(Integer)       
    actual_home_goals = Column(Integer, nullable=True)
    actual_away_goals = Column(Integer, nullable=True)
    
    # GOLD MINE
    is_settled = Column(Boolean, default=False)
    raw_data = Column(JSON, nullable=True) 

    # 💰 PERFORMANCE LOG
    system_bet_pl = Column(Float, default=0.0)
    system_bet_info = Column(JSON, nullable=True)