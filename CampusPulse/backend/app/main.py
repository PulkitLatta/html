from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decouple import config
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.models import Base
from app.api import submissions, athletes, admin
from app.utils.auth import get_current_user

# Configuration
DATABASE_URL = config('DATABASE_URL', default='postgresql://user:password@localhost/campuspulse')
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')
JWT_SECRET = config('JWT_SECRET', default='your-secret-key-change-in-production')

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

# Global variables for DB and Redis
engine = None
SessionLocal = None
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global engine, SessionLocal, redis_client
    
    # Initialize database
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables (in production, use Alembic migrations)
    Base.metadata.create_all(bind=engine)
    
    # Initialize Redis
    try:
        redis_client = redis.from_url(REDIS_URL)
        await redis_client.ping()
        print("✅ Redis connected successfully")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        redis_client = None
    
    print("🚀 CampusPulse Backend started successfully")
    
    yield
    
    # Shutdown
    if redis_client:
        redis_client.close()
    if engine:
        engine.dispose()
    print("👋 CampusPulse Backend shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="CampusPulse API",
    description="Athletic Performance Analytics API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.campuspulse.com"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(submissions.router, prefix="/api/submissions", tags=["submissions"])
app.include_router(athletes.router, prefix="/api/athletes", tags=["athletes"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "CampusPulse API",
        "version": "1.0.0",
        "status": "online",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "submissions": "/api/submissions",
            "athletes": "/api/athletes",
            "admin": "/api/admin",
        }
    }

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint for monitoring"""
    db_status = "connected"
    redis_status = "connected" if redis_client else "disconnected"
    
    try:
        # Test DB connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_status = "error"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "redis": redis_status,
        "version": "1.0.0"
    }

@app.post("/api/assistant")
@limiter.limit("10/minute")
async def assistant_endpoint(request: Request, background_tasks: BackgroundTasks):
    """AI assistant endpoint for technique analysis"""
    # This would integrate with an LLM for exercise technique advice
    return {
        "message": "AI assistant endpoint - would provide technique analysis and recommendations",
        "status": "placeholder",
        "note": "Integrate with OpenAI or similar service for production"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )