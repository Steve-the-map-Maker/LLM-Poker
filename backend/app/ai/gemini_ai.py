try:
    import google.generativeai as genai
except ImportError:
    genai = None
import pokerkit
import asyncio
import time
from typing import List, Optional
from app.ai.base_ai import AIPlayer
from app.api.v1.poker_schemas import PlayerActionRequest
from app.ai.llm_prompts import format_poker_state_for_llm
from app.config import settings

class GeminiAI(AIPlayer):
    # Class-level rate limiting (shared across all instances)
    _last_request_time = 0
    _min_request_interval = 4.5  # 4.5 seconds = ~13 RPM (safe margin under 15 RPM limit)
    
    def __init__(self, model_name: str = "gemini-2.5-flash-lite"):
        # Prioritize GEMINI_API_KEY as per .env standard
        self.api_key = settings.GEMINI_API_KEY
        self.model = None
        self.model_name = model_name
        self.last_error: Optional[str] = None  # Track last error for visibility
        if not self.api_key:
            print("Warning: GEMINI_API_KEY not found. Gemini AI will fail.")
        else:
            try:
                genai.configure(api_key=self.api_key)
                # Use model specified by user (or default to flash-lite for best free tier)
                self.model = genai.GenerativeModel(model_name)
                print(f"GeminiAI initialized with model: {model_name}")
            except Exception as e:
                print(f"Error configuring Gemini AI: {e}")
    
    async def get_action(self, pk_state: pokerkit.State, player_index: int, game_id: str, player_name: str) -> PlayerActionRequest:
        # Clear previous error
        self.last_error = None
        
        # 1. Format state into prompt
        prompt = format_poker_state_for_llm(pk_state, player_index, game_id, player_name, [])
        print(f"\n--- Prompt for {player_name} (Gemini: {self.model_name}) ---")
        print(prompt)
        print("-----------------------------------\n")
        
        llm_response_text = None
        max_retries = 3
        
        # 2. Proactive rate limiting - ensure minimum time between requests
        current_time = time.time()
        time_since_last = current_time - GeminiAI._last_request_time
        if time_since_last < GeminiAI._min_request_interval:
            wait_time = GeminiAI._min_request_interval - time_since_last
            print(f"Rate limiting: waiting {wait_time:.1f}s before API call...")
            await asyncio.sleep(wait_time)
        
        # 3. Make API call to LLM with retry logic
        rate_limit_hit = False
        for attempt in range(max_retries):
            try:
                if not self.model:
                    raise ValueError("Gemini model not initialized")
                
                GeminiAI._last_request_time = time.time()  # Update before call
                response = await self.model.generate_content_async(prompt)
                llm_response_text = response.text.strip()
                print(f"Gemini Raw Response for {player_name}: {llm_response_text}")
                break  # Success, exit retry loop
                
            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower()
                
                if is_rate_limit:
                    rate_limit_hit = True
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                        print(f"Rate limit hit for {player_name}. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        self.last_error = f"⚠️ RATE LIMITED: {player_name} forced to fold (Gemini API quota exceeded after {max_retries} retries)"
                        print(self.last_error)
                        return PlayerActionRequest(action_type="fold")
                else:
                    print(f"Error calling LLM API for {player_name} (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        self.last_error = f"⚠️ API ERROR: {player_name} forced to fold ({type(e).__name__})"
                        print(self.last_error)
                        return PlayerActionRequest(action_type="fold")
        
        # 4. Parse LLM's text response into PlayerActionRequest
        parts = llm_response_text.upper().split() if llm_response_text else []
        action_type_str = parts[0] if parts else "FOLD"
        
        if action_type_str == "FOLD": 
            return PlayerActionRequest(action_type="fold")
        elif action_type_str == "CHECK": 
            return PlayerActionRequest(action_type="check")
        elif action_type_str == "CALL":
            return PlayerActionRequest(action_type="call")
        elif action_type_str == "RAISE_TO" and len(parts) > 1:
            try:
                amount = int(parts[1])
                return PlayerActionRequest(action_type="raise", amount=amount)
            except ValueError:
                self.last_error = f"Parse error: Invalid raise amount from {player_name}"
                print(f"LLM {player_name} response parsing error (invalid raise amount): {llm_response_text}")
                return PlayerActionRequest(action_type="fold")
        else:
            self.last_error = f"Parse error: Unknown action '{action_type_str}' from {player_name}"
            print(f"LLM {player_name} response parsing error (unknown action): {llm_response_text}")
            return PlayerActionRequest(action_type="fold")
