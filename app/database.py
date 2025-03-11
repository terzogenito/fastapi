# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Database URL (Replace with your actual database credentials)
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost/fastapidb"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=True)
# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
