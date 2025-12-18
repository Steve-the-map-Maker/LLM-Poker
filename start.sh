#!/bin/bash

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping servers..."
    kill $(jobs -p)
    exit
}

trap cleanup SIGINT

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Backend Server (FastAPI)..."
cd "$ROOT_DIR/backend"
source venv/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting Frontend Server (React)..."
cd "$ROOT_DIR/frontend"
PORT=3000 BROWSER=none npm start &
FRONTEND_PID=$!

echo "--------------------------------------------------"
echo "Servers are running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both servers."
echo "--------------------------------------------------"

wait
