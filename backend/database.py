# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the URL from Railway environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# If testing locally without Railway, use a local file (SQLite)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./edgelock.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()