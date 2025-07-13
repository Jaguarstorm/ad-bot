# backend/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime, timedelta

from backend.utils.database import get_supabase_client, create_user_profile, get_user_by_id
from backend.utils.crypto_utils import create_jwt_token, verify_jwt_token
from backend.config import ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Pydantic models
class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    plan: str

class UserProfile(BaseModel):
    id: str
    email: str
    plan: str
    trial_start: Optional[str] = None
    created_at: str

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register new user"""
    try:
        supabase = get_supabase_client()
        
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if auth_response.user:
            user_id = auth_response.user.id
            
            # Create user profile
            await create_user_profile(
                user_id=user_id,
                email=user_data.email,
                plan="trial"
            )
            
            # Create access token
            access_token = create_jwt_token(
                data={"sub": user_id},
                expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user_id,
                plan="trial"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user"""
    try:
        supabase = get_supabase_client()
        
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if auth_response.user:
            user_id = auth_response.user.id
            
            # Get user profile
            user_profile = await get_user_by_id(user_id)
            if not user_profile:
                # Create profile if it doesn't exist
                await create_user_profile(user_id, user_data.email, "trial")
                plan = "trial"
            else:
                plan = user_profile.get("plan", "trial")
            
            # Create access token
            access_token = create_jwt_token(
                data={"sub": user_id},
                expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user_id=user_id,
                plan=plan
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.get("/profile", response_model=UserProfile)
async def get_profile(user_id: str = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_profile = await get_user_by_id(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        return UserProfile(**user_profile)
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )

@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user)):
    """Logout user (client should discard token)"""
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/refresh")
async def refresh_token(user_id: str = Depends(get_current_user)):
    """Refresh access token"""
    try:
        # Create new access token
        access_token = create_jwt_token(
            data={"sub": user_id},
            expires_delta=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/agree-terms")
async def agree_to_terms(user_id: str = Depends(get_current_user)):
    """Record user agreement to terms and conditions"""
    try:
        supabase = get_supabase_client()
        
        # Check if already agreed
        existing = supabase.table("user_agreements").select("*").eq("user_id", user_id).execute()
        
        if not existing.data:
            # Record agreement
            supabase.table("user_agreements").insert({
                "user_id": user_id,
                "agreed_at": "now()",
                "app_version": "1.0.0"
            }).execute()
        
        return {"status": "agreed"}
    except Exception as e:
        logger.error(f"Terms agreement error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record agreement"
        )

@router.get("/has-agreed")
async def check_agreement(user_id: str = Depends(get_current_user)):
    """Check if user has agreed to terms"""
    try:
        supabase = get_supabase_client()
        result = supabase.table("user_agreements").select("*").eq("user_id", user_id).execute()
        return {"agreed": len(result.data) > 0}
    except Exception as e:
        logger.error(f"Check agreement error: {e}")
        return {"agreed": False} 