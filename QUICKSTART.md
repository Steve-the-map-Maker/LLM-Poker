# 🚀 Quick Start Guide

To get the LLM Poker Arena up and running quickly, follow these steps:

## Option 1: One-Command Start (Recommended)
We've provided a script to start both the frontend and backend in a single terminal window.

1. Open your terminal in the project root.
2. Run the start script:
   ```bash
   ./start.sh
   ```
3. Open **[http://localhost:3000](http://localhost:3000)** in your browser.

## Option 2: Manual Start (Two Terminals)
If you prefer to see separate logs, use two terminal tabs:

### 1. Start the Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```
*Backend will be at: http://localhost:8000*

### 2. Start the Frontend
```bash
cd frontend
npm start
```
*Frontend will be at: http://localhost:3000*

---

## Troubleshooting
- **Port already in use**: If you get an error that port 8000 or 3000 is busy, make sure no other instances are running.
- **Dependencies**: If this is your first time, run `pip install -r requirements.txt` in the `backend` folder and `npm install` in the `frontend` folder.
- **Environment Variables**: Ensure `backend/.env` exists and contains your `GEMINI_API_KEY` or `OPENAI_API_KEY`.
