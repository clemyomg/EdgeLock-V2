import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv  # 👈 THIS IS KEY

# 1. Load your secret .env file
load_dotenv()

# 2. Get the link
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Fallback check
if not DATABASE_URL:
    print("⚠️ No DATABASE_URL found. Using local SQLite.")
    DATABASE_URL = "sqlite:///./edgelock.db"

# 4. Railway Fix
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

try:
    # 5. Connection Setup
    connect_args = {}
    if "sqlite" not in DATABASE_URL:
        connect_args = {"sslmode": "require"}

    print(f"🔌 Connecting to Database...") 
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    
    # Test connection
    with engine.connect() as connection:
        print("✅ Database Connection Successful!")

except Exception as e:
    print(f"❌ Database Config Error: {e}")
    print("⚠️ Critical Error: Falling back to temporary SQLite database.")
    engine = create_engine("sqlite:///./edgelock.db")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()