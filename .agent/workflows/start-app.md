---
description: How to start both the frontend and backend servers
---

To start the LLM Poker Arena:

// turbo
1. Run the unified start script from the root directory:
   ```bash
   ./start.sh
   ```

2. Alternatively, start them manually in separate terminals:
   
   **Backend:**
   ```bash
   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000
   ```

   **Frontend:**
   ```bash
   cd frontend && npm start
   ```

3. Open the game in your browser:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)
