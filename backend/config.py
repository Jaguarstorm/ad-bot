# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# App Configuration
APP_NAME = "AdForgeAI"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Database Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# AI Services
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Billing Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Google Play Billing (Android)
GOOGLE_PLAY_PACKAGE_NAME = os.getenv("GOOGLE_PLAY_PACKAGE_NAME", "com.jaguarstorm.adforgeai")
GOOGLE_PLAY_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_KEY")

# Social Media API Keys
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")
TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")

# Security
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
TOKEN_AES_SECRET = os.getenv("TOKEN_AES_SECRET", "your-32-char-aes-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# File Storage
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_VIDEO_TYPES = [".mp4", ".mov", ".avi", ".mkv"]
ALLOWED_IMAGE_TYPES = [".jpg", ".jpeg", ".png", ".gif"]

# Usage Limits
BASIC_PLAN_LIMITS = {
    "daily_uploads": 5,
    "daily_ai_captions": 30,
    "daily_subtitles": 20,
    "storage_gb": 2,
    "monthly_videos": 30
}

PRO_PLAN_LIMITS = {
    "daily_uploads": 50,
    "daily_ai_captions": 100,
    "daily_subtitles": 100,
    "storage_gb": 10,
    "monthly_videos": 500
}

TRIAL_LIMITS = {
    "daily_uploads": 3,
    "daily_ai_captions": 10,
    "daily_subtitles": 5,
    "storage_gb": 0.5,
    "trial_days": 15
}

# Video Processing
MAX_VIDEO_DURATION = 300  # 5 minutes
SUPPORTED_ASPECT_RATIOS = {
    "tiktok": (9, 16),
    "youtube_shorts": (9, 16),
    "instagram_reels": (9, 16),
    "instagram_post": (1, 1),
    "youtube": (16, 9)
}

# AI Configuration
GPT_MODEL = "gpt-4o"
MAX_TOKENS = 1000
TEMPERATURE = 0.7

# Email Configuration (for notifications)
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@adforgeai.com")

# Redis (for caching and background tasks)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "adforgeai.log")

# Feature Flags
ENABLE_AI_VIDEO_GENERATOR = os.getenv("ENABLE_AI_VIDEO_GENERATOR", "true").lower() == "true"
ENABLE_AUTO_POSTING = os.getenv("ENABLE_AUTO_POSTING", "true").lower() == "true"
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true" 