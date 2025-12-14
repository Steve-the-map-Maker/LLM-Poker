try:
    import openai
except ImportError:
    openai = None
import pokerkit
import asyncio
import time
from typing import List, Optional
from app.ai.base_ai import AIPlayer
from app.api.v1.poker_schemas import PlayerActionRequest
from app.ai.llm_prompts import format_poker_state_for_llm
from app.config import settings

class GPTAI(AIPlayer):
    # Class-level rate limiting (shared across all instances)
    _last_request_time = 0
    _min_request_interval = 1.0  # 1 second between requests (OpenAI has higher limits)
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = model_name
        self.client = None
        self.last_error: Optional[str] = None  # Track last error for visibility
        
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found. GPT AI will fail.")
        elif not openai:
            print("Warning: openai library not installed. GPT AI will fail.")
        else:
            # Initialize OpenAI client
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            print(f"GPTAI initialized with model: {model_name}")
    
    async def get_action(self, pk_state: pokerkit.State, player_index: int, game_id: str, player_name: str) -> PlayerActionRequest:
        # Clear previous error
        self.last_error = None
        
        # 1. Format state into prompt
        prompt = format_poker_state_for_llm(pk_state, player_index, game_id, player_name, [])
        print(f"\n--- Prompt for {player_name} (GPT: {self.model_name}) ---")
        print(prompt)
        print("-----------------------------------\n")
        llm_response_text = None
        max_retries = 3
        
        # 2. Proactive rate limiting
        current_time = time.time()
        time_since_last = current_time - GPTAI._last_request_time
        if time_since_last < GPTAI._min_request_interval:
            wait_time = GPTAI._min_request_interval - time_since_last
            print(f"Rate limiting: waiting {wait_time:.1f}s before GPT API call...")
            await asyncio.sleep(wait_time)
        
        # 3. Make API call with retry logic
        for attempt in range(max_retries):
            try:
                if not self.client:
                    raise ValueError("OpenAI client not initialized")
                
                GPTAI._last_request_time = time.time()
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50, 
                    temperature=0.7
                )
                llm_response_text = response.choices[0].message.content.strip()
                print(f"GPT Raw Response for {player_name}: {llm_response_text}")
                break  # Success
                
            except Exception as e:
                error_str = str(e)
                is_rate_limit = "429" in error_str or "rate" in error_str.lower()
                
                if is_rate_limit:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # 3s, 6s, 9s
                        print(f"GPT rate limit hit. Retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        self.last_error = f"⚠️ RATE LIMITED: {player_name} forced to fold (OpenAI API quota exceeded after {max_retries} retries)"
                        print(self.last_error)
                        return PlayerActionRequest(action_type="fold")
                else:
                    print(f"Error calling GPT API for {player_name} (attempt {attempt + 1}): {e}")
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
