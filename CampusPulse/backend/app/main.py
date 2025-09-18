import os
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis.asyncio as redis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.api import submissions, athletes, admin
from app.models import Base
from app.utils.auth import get_current_user
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/campuspulse")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis setup for rate limiting and caching
redis_client = None

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup
    logger.info("Starting CampusPulse API server...")
    
    # Initialize Redis connection
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info(f"Connected to Redis at {redis_url}")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        redis_client = None

    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CampusPulse API server...")
    if redis_client:
        await redis_client.close()

# Create FastAPI app with lifespan manager
app = FastAPI(
    title="CampusPulse API",
    description="AI-powered athletic performance analysis platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    """Health check endpoint for monitoring."""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database connection
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis connection
    if redis_client:
        try:
            await redis_client.ping()
            health_status["redis"] = "connected"
        except Exception as e:
            health_status["redis"] = f"error: {str(e)}"
    else:
        health_status["redis"] = "not_configured"
    
    return health_status

# AI Assistant endpoint (placeholder for future AI integration)
@app.post("/api/assistant")
@limiter.limit("10/minute")
async def ai_assistant(request: Request, query: Dict[str, Any]):
    """AI assistant endpoint for athlete guidance and insights."""
    user = await get_current_user(request)
    
    # Placeholder response - would integrate with actual AI service
    return {
        "response": "AI assistant feature coming soon! Your query has been received.",
        "query": query.get("message", ""),
        "user_id": user.get("user_id") if user else None,
        "suggestions": [
            "Try recording a new training session",
            "Check your recent performance metrics",
            "View the leaderboard for motivation"
        ]
    }

# Include API routers
app.include_router(submissions.router, prefix="/api", tags=["submissions"])
app.include_router(athletes.router, prefix="/api", tags=["athletes"])  
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Welcome to CampusPulse API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return {"error": "Endpoint not found", "path": str(request.url.path)}

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return {"error": "Internal server error", "message": "Please try again later"}

# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for monitoring."""
    start_time = asyncio.get_event_loop().time()
    
    # Process request
    response = await call_next(request)
    
    # Log request details
    duration = asyncio.get_event_loop().time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Duration: {duration:.3f}s"
    )
    
    return response

# Utility function to get Redis client
def get_redis():
    """Get Redis client instance."""
    return redis_client

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )