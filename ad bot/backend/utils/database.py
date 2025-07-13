# backend/utils/database.py
from supabase import create_client, Client
from backend.config import SUPABASE_URL, SUPABASE_KEY
import logging

logger = logging.getLogger(__name__)

# Global Supabase client
supabase: Client = None

async def init_db():
    """Initialize database connection"""
    global supabase
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Database connection established")
        
        # Create tables if they don't exist
        await create_tables()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    if supabase is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return supabase

async def create_tables():
    """Create database tables if they don't exist"""
    try:
        # Users table (extends Supabase auth.users)
        supabase.table("user_profiles").select("id").limit(1).execute()
        logger.info("User profiles table exists")
    except:
        # Create user_profiles table
        supabase.rpc("create_user_profiles_table").execute()
        logger.info("Created user_profiles table")

    try:
        # User tokens table
        supabase.table("user_tokens").select("id").limit(1).execute()
        logger.info("User tokens table exists")
    except:
        # Create user_tokens table
        supabase.rpc("create_user_tokens_table").execute()
        logger.info("Created user_tokens table")

    try:
        # Videos table
        supabase.table("videos").select("id").limit(1).execute()
        logger.info("Videos table exists")
    except:
        # Create videos table
        supabase.rpc("create_videos_table").execute()
        logger.info("Created videos table")

    try:
        # Scheduled posts table
        supabase.table("scheduled_posts").select("id").limit(1).execute()
        logger.info("Scheduled posts table exists")
    except:
        # Create scheduled_posts table
        supabase.rpc("create_scheduled_posts_table").execute()
        logger.info("Created scheduled_posts table")

    try:
        # User agreements table
        supabase.table("user_agreements").select("id").limit(1).execute()
        logger.info("User agreements table exists")
    except:
        # Create user_agreements table
        supabase.rpc("create_user_agreements_table").execute()
        logger.info("Created user_agreements table")

    try:
        # Subscriptions table
        supabase.table("subscriptions").select("id").limit(1).execute()
        logger.info("Subscriptions table exists")
    except:
        # Create subscriptions table
        supabase.rpc("create_subscriptions_table").execute()
        logger.info("Created subscriptions table")

    try:
        # Analytics table
        supabase.table("analytics").select("id").limit(1).execute()
        logger.info("Analytics table exists")
    except:
        # Create analytics table
        supabase.rpc("create_analytics_table").execute()
        logger.info("Created analytics table")

async def get_user_by_id(user_id: str):
    """Get user profile by ID"""
    try:
        result = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

async def create_user_profile(user_id: str, email: str, plan: str = "trial"):
    """Create user profile"""
    try:
        result = supabase.table("user_profiles").insert({
            "id": user_id,
            "email": email,
            "plan": plan,
            "trial_start": "now()",
            "created_at": "now()"
        }).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return None

async def update_user_plan(user_id: str, plan: str):
    """Update user subscription plan"""
    try:
        result = supabase.table("user_profiles").update({
            "plan": plan,
            "updated_at": "now()"
        }).eq("id", user_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating user plan: {e}")
        return None

async def get_user_usage(user_id: str):
    """Get user usage statistics"""
    try:
        # Get daily usage
        today = "now()::date"
        result = supabase.table("analytics").select("*").eq("user_id", user_id).eq("date", today).execute()
        return result.data[0] if result.data else {"uploads": 0, "ai_captions": 0, "subtitles": 0}
    except Exception as e:
        logger.error(f"Error getting user usage: {e}")
        return {"uploads": 0, "ai_captions": 0, "subtitles": 0}

async def increment_usage(user_id: str, usage_type: str):
    """Increment user usage counter"""
    try:
        today = "now()::date"
        # Try to update existing record
        result = supabase.table("analytics").update({
            usage_type: f"{usage_type} + 1"
        }).eq("user_id", user_id).eq("date", today).execute()
        
        if not result.data:
            # Create new record
            supabase.table("analytics").insert({
                "user_id": user_id,
                "date": today,
                usage_type: 1
            }).execute()
            
    except Exception as e:
        logger.error(f"Error incrementing usage: {e}") 