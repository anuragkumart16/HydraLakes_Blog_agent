import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
import jwt
from db.client import db
from db.models.user_model import UserCreate, UserLogin, UserResponse

auth_router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET not found in environment variables")

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_val = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
    return f"{salt}:{hash_val}"

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        salt, stored_hash = hashed_password.split(":")
        hash_val = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        return secrets.compare_digest(hash_val, stored_hash)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    # Check if user with same email or username already exists
    existing_user = await db.users.find_one({"$or": [{"email": user.email}, {"username": user.username}]})
    if existing_user:
        if existing_user.get("email") == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )

    hashed_pwd = hash_password(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": hashed_pwd
    }

    result = await db.users.insert_one(user_dict)
    user_id = str(result.inserted_id)

    access_token = create_access_token(
        data={"sub": user_id, "email": user.email, "username": user.username}
    )

    return {
        "message": "User created successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user_id,
            username=user.username,
            email=user.email
        )
    }

@auth_router.post("/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user_id = str(user["_id"])
    access_token = create_access_token(
        data={"sub": user_id, "email": user["email"], "username": user["username"]}
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user_id,
            username=user["username"],
            email=user["email"]
        )
    }

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token"
        )

@auth_router.post("/password-login")
async def password_login(credentials: UserLogin):
    return await login(credentials)

@auth_router.get("/me")
async def get_current_user_profile(token: str | None = None):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing"
        )
    payload = decode_access_token(token)
    return {"user": payload}