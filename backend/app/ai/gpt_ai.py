import openai
import pokerkit
from typing import List
from app.ai.base_ai import AIPlayer
from app.api.v1.poker_schemas import PlayerActionRequest
from app.ai.llm_prompts import format_poker_state_for_llm
from app.config import settings

class GPTAI(AIPlayer):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("API key for OpenAI not found.")
        
        # Initialize OpenAI client
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
    
    async def get_action(self, pk_state: pokerkit.State, player_index: int, game_id: str, player_name: str) -> PlayerActionRequest:
        # 1. Format state into prompt
        # Note: history for the prompt might be just pk_state.operations, or a separately maintained list of action strings.
        # For now, format_poker_state_for_llm handles operations internally.
        prompt = format_poker_state_for_llm(pk_state, player_index, game_id, player_name, [])
        print(f"\n--- Prompt for {player_name} (GPT) ---")
        print(prompt)
        print("-----------------------------------\n")
        llm_response_text = None
        # 2. Make API call to LLM
        try:
            # Example for OpenAI:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # or "gpt-4"
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50, 
                temperature=0.5
            )
            llm_response_text = response.choices[0].message.content.strip()
            print(f"GPT Raw Response for {player_name}: {llm_response_text}")
        except Exception as e:
            print(f"Error calling LLM API for {player_name}: {e}")
            return PlayerActionRequest(action_type="fold")  # Default to fold on API error
        
        # 3. Parse LLM's text response into PlayerActionRequest
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
                print(f"LLM {player_name} response parsing error (invalid raise amount): {llm_response_text}")
                return PlayerActionRequest(action_type="fold")  # Default action
        else:
            print(f"LLM {player_name} response parsing error (unknown action): {llm_response_text}")
            return PlayerActionRequest(action_type="fold")  # Default action
