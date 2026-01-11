import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the URL from Railway environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# 1. Fallback for local testing
if not DATABASE_URL:
    print("⚠️ No DATABASE_URL found. Using local SQLite.")
    DATABASE_URL = "sqlite:///./edgelock.db"

# 2. Fix for Railway/Heroku "postgres://" URLs
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    # 3. SSL Fix for Public Connections
    connect_args = {}
    if "sqlite" not in DATABASE_URL:
        # Public URLs usually need SSL
        connect_args = {"sslmode": "require"}

    print(f"🔌 Connecting to Database...") 
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    
    # Test connection immediately
    with engine.connect() as connection:
        print("✅ Database Connection Successful!")

except Exception as e:
    print(f"❌ Database Config Error: {e}")
    print("⚠️ Critical Error: Falling back to temporary SQLite database.")
    # Fallback prevents crash loop
    engine = create_engine("sqlite:///./edgelock.db")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()