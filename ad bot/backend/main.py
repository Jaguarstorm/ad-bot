# backend/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
from datetime import datetime

# Import routers
from backend.api import auth, upload, editor, generator, social, billing, analytics
from backend.tasks.scheduler import start_post_scheduler
from backend.utils.database import init_db

# Create FastAPI app
app = FastAPI(
    title="AdForgeAI API",
    description="AI-Powered Video Creation & Social Media Automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload.router, prefix="/api/upload", tags=["Video Upload"])
app.include_router(editor.router, prefix="/api/editor", tags=["Smart Editor"])
app.include_router(generator.router, prefix="/api/generator", tags=["AI Generator"])
app.include_router(social.router, prefix="/api/social", tags=["Social Media"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "AdForgeAI API - Jaguar Storm",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and start background tasks"""
    await init_db()
    # Start post scheduler in background
    asyncio.create_task(start_post_scheduler())

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down AdForgeAI API...")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 