from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.endpoints import game as game_api_v1
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("poker_arena")

app = FastAPI(
    title="LLM Poker Arena API",
    version="0.1.0",
    description="API for managing poker games between LLMs and humans."
)

# Global exception handler - sanitize errors in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return sanitized error message."""
    # Log the full error for debugging
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    
    # Return sanitized error to client (don't expose stack traces)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again.",
            "error_type": type(exc).__name__
        }
    )

# CORS Middleware Configuration
origins = [
    "http://localhost:3000",  # Allow your React frontend
]

# Add production frontend URL if set
if os.getenv("FRONTEND_URL"):
    origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the v1 game router
app.include_router(game_api_v1.router, prefix="/api/v1/game", tags=["Game"])

@app.get("/ping")
async def ping():
    """Simple health check."""
    return {"message": "pong"}

@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint for monitoring.
    Returns API status and game statistics.
    """
    # Import here to avoid circular imports
    from app.api.v1.endpoints.game import poker_game_manager
    
    stats = poker_game_manager.get_game_stats()
    
    return {
        "status": "healthy",
        "version": "0.1.0",
        "games": stats
    }

