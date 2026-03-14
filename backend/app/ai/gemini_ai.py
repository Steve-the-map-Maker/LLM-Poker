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
    _min_request_interval = 1.0  # Reduced to 1.0s for paid tier (mostly to prevent race conditions)
    
    def __init__(self, model_name: str = "gemini-3.1-flash-lite-preview", custom_prompt: str = None):
        # Prioritize GEMINI_API_KEY as per .env standard
        self.api_key = settings.GEMINI_API_KEY
        self.model = None
        self.model_name = model_name
        self.custom_prompt = custom_prompt  # User-defined AI personality
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
        
        # 1. Format state into prompt (pass custom_prompt for personalized AI behavior)
        prompt = format_poker_state_for_llm(pk_state, player_index, game_id, player_name, [], self.custom_prompt)
        # Add strict formatting instruction for Gemini 3.1 which tends to be talkative
        prompt += "\n\nCRITICAL: You must include one of these EXACT strings in your response: FOLD, CHECK, CALL, or RAISE_TO <amount>."
        
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
                is_rate_limit = "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower()
                
                if is_rate_limit:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2s, 4s, 6s (faster retries for paid tier)
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
        # Robust parsing: look for keywords in the entire response
        text = llm_response_text.upper()
        
        # Check for RAISE_TO first since it contains a number
        import re
        raise_match = re.search(r'RAISE_TO\s+(\d+)', text)
        if raise_match:
            try:
                amount = int(raise_match.group(1))
                return PlayerActionRequest(action_type="raise", amount=amount, reasoning=llm_response_text)
            except ValueError:
                pass # Fall through to other keywords

        if "FOLD" in text:
            return PlayerActionRequest(action_type="fold", reasoning=llm_response_text)
        if "CHECK" in text:
            return PlayerActionRequest(action_type="check", reasoning=llm_response_text)
        if "CALL" in text:
            return PlayerActionRequest(action_type="call", reasoning=llm_response_text)
            
        # If no keywords found, but it gave a raw number, assume it's a raise? 
        # Better to be safe and try one more thing: just the first word
        parts = text.split()
        if parts:
            if parts[0] == "FOLD": return PlayerActionRequest(action_type="fold", reasoning=llm_response_text)
            if parts[0] == "CHECK": return PlayerActionRequest(action_type="check", reasoning=llm_response_text)
            if parts[0] == "CALL": return PlayerActionRequest(action_type="call", reasoning=llm_response_text)

        self.last_error = f"Parse error: Could not find valid action in '{llm_response_text[:50]}...'"
        print(f"LLM {player_name} response parsing error: {llm_response_text}")
        return PlayerActionRequest(action_type="fold", reasoning=llm_response_text)
