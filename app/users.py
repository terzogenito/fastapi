# app/users.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import jwt
from .auth import (
    create_access_token, 
    verify_token, 
    verify_password, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM,
)
from .models import User, path, TokenBlacklist  # Import the User model
from .database import get_db  # Dependency to get the database session

path = f"/{path['users']}/"

# Create an APIRouter instance
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # URL token

# Define Pydantic model for the response without the password
class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        # Update to Pydantic V2
        from_attributes = True  # Replaces 'orm_mode = True' in V2

# FastAPI route to get the list of all users
@router.get(f"{path}", response_model=list[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    db_users = db.query(User).all()  # Fetch all users
    # Return a list of UserResponse objects
    return [UserResponse.from_orm(user) for user in db_users]

# FastAPI route to get a user by ID (returns user details)
@router.get(f"{path}{{user_id}}")
async def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Define Pydantic model for user input
class UserCreateRequest(BaseModel):
    email: str
    password: str

# FastAPI route to create a user
@router.post(f"{path}")
async def create_user(user: UserCreateRequest, db: Session = Depends(get_db)):
    # Access data from the Pydantic model
    db_user = User(email=user.email)
    db_user.set_password(user.password)  # Hash the password before saving it
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Define Pydantic model for updating a user
class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

@router.put(f"{path}{{user_id}}", response_model=UserResponse)  # Specify response_model
async def update_user(
    user_id: int, 
    user_update: UserUpdateRequest,  # Use the Pydantic model for the request body
    db: Session = Depends(get_db)
):
    # Fetch the user from the database
    db_user = db.query(User).filter(User.id == user_id).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields if provided in the request body
    if user_update.email:
        db_user.email = user_update.email
    if user_update.password:
        db_user.set_password(user_update.password)  # Hash the new password before storing it

    # Commit changes to the database
    db.commit()
    db.refresh(db_user)

    # Return the user without the password field
    return db_user  # Since response_model is specified, it will be converted to UserResponse

@router.delete(f"{path}{{user_id}}")
async def delete_user(user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Pass the token to verify_token, which checks if it is blacklisted
    verify_token(token, db)

    # Check if the user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user
    db.delete(db_user)
    db.commit()
    return {"message": f"User with id {user_id} has been deleted successfully."}

# Pydantic model for authentication request
class UserAuthRequest(BaseModel):
    email: str
    password: str

@router.post(f"{path}authenticate")
async def authenticate_user(auth_request: UserAuthRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == auth_request.email).first()
    
    if db_user is None or not db_user.verify_password(auth_request.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create the JWT token using the utility function
    token_data = {"sub": db_user.email}  # 'sub' is a standard claim for the subject (usually the email)
    access_token = create_access_token(data=token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}

# Custom input model for JSON requests
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post(f"{path}login")
async def login(
    login_request: LoginRequest,  # Accept JSON input
    db: Session = Depends(get_db)
):
    # Authenticate user using email and password
    user = db.query(User).filter(User.email == login_request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify the provided password
    if not verify_password(login_request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@router.post(f"{path}logout")
async def logout_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Add the token to the blacklist
        expires_at = datetime.utcfromtimestamp(payload["exp"])
        blacklisted_token = TokenBlacklist(token=token, expires_at=expires_at)
        db.add(blacklisted_token)
        db.commit()

        return {"message": "Logout successful"}
    except jwt.ExpiredSignatureError:
        return {"message": "Token has already expired."}
    except jwt.PyJWTError:
        return {"message": "Invalid token."}

