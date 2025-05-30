from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import game as game_api_v1

app = FastAPI(
    title="LLM Poker Arena API",
    version="0.1.0",
    description="API for managing poker games between LLMs and humans."
)

# CORS Middleware Configuration
origins = [
    "http://localhost:3000",  # Allow your React frontend
    # You can add other origins here if needed, e.g., your deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include the v1 game router
app.include_router(game_api_v1.router, prefix="/api/v1/game", tags=["Game"])

@app.get("/ping")
async def ping():
    return {"message": "pong"}

# If you have other routers or global configurations, they would go here.
