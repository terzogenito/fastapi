# app/models.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
# from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from passlib.context import CryptContext

# Define the Base for SQLAlchemy models
Base = declarative_base()

# Set up the password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

path = {
    "users": "users",
    "token_blacklist": "token_blacklist"
}

# Example model: Users
class User(Base):
    __tablename__ = path['users']

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    def set_password(self, password: str):
        """Hash the password before storing it."""
        self.password = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """Verify the password against the hashed version."""
        return pwd_context.verify(password, self.password)

class TokenBlacklist(Base):
    __tablename__ = path['token_blacklist']

    token = Column(String, primary_key=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    def __init__(self, token: str, expires_at: datetime):
        self.token = token
        self.expires_at = expires_at