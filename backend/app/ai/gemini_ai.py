import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from typing import Dict, Any, Optional

from app.ai.base_ai import AIPlayer
from .llm_prompts import format_poker_state_for_llm

# Load environment variables from .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_gemini_configured_successfully = False # Module-level flag

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_configured_successfully = True
        print("Gemini API configured successfully at module level.")
    except Exception as e:
        print(f"Error configuring Gemini API at module level: {e}. Ensure your API key is valid and has permissions.")

class GeminiAI(AIPlayer):
    def __init__(self, model_name: str = "gemini-1.5-flash-latest", player_name: str = "Gemini AI"):
        super().__init__(player_name)
        self.model_name = model_name
        self.model = None # Initialize model as None
        
        if _gemini_configured_successfully: # Check module-level flag
            try:
                self.model = genai.GenerativeModel(self.model_name)
                print(f"Gemini model ({self.model_name}) initialized successfully for {self.player_name}.")
            except Exception as e:
                print(f"Error initializing Gemini model ({self.model_name}) for {self.player_name} after successful configuration: {e}. AI will use fallback logic.")
                self.model = None # Ensure model is None if initialization fails
        else:
            print(f"Gemini AI ({self.player_name}) not initialized because API key was missing or configuration failed at module level. AI will use fallback logic.")

    async def get_action(self, pk_state: Any, player_index: int, game_id: str, player_name: str) -> Dict[str, Any]: # Changed game_state to pk_state and added async
        """
        Uses the Gemini LLM to decide on a poker action.
        Method signature now matches BaseAI.
        """
        if not self.model:
            print(f"Gemini model ({self.model_name}) for {self.player_name} not available. Falling back to default action.")
            print(f"Warning: _fallback_action in GeminiAI called. pk_state type: {type(pk_state)}")
            return {"action_type": "fold"} # Simplified fallback, ensure this matches expected return type

        # Placeholder for pk_state to game_state_dict conversion
        game_state_dict = {
            "variant": "No-Limit Texas Hold'em", # Example, derive from pk_state
            "initial_bet_size": pk_state.small_blind_amount if hasattr(pk_state, 'small_blind_amount') else 1,
            "actor_index": pk_state.actor_index,
            "street_name": pk_state.street_name if hasattr(pk_state, 'street_name') else "Unknown Street",
            "hole_cards": [list(map(str, cards)) if cards else [] for cards in pk_state.hole_cards],
            "community_cards": list(map(str, pk_state.community_cards)),
            "stacks": list(pk_state.stacks),
            "pot_contributions": list(pk_state.pot_contributions()) if hasattr(pk_state, 'pot_contributions') and callable(pk_state.pot_contributions) else [0,0], # pokerkit 0.7.0
            "available_actions": [action.name.lower().replace(' ', '_') for action in pk_state.legal_actions],
            "checking_or_calling_amount": pk_state.checking_or_calling_amount,
            "min_raise_to_amount": pk_state.min_raise_to_amount if pk_state.can_complete_bet_or_raise_to() else 0,
            "max_raise_to_amount": pk_state.stacks[player_index] if pk_state.can_complete_bet_or_raise_to() else 0, # Simplification
            "player_identities": [p.player_name for p in pk_state.players] if hasattr(pk_state, 'players') and pk_state.players and hasattr(pk_state.players[0], 'player_name') else ["Player 0", "Player 1"], # Placeholder
            "last_action_details": None, # Placeholder
            "pot_total": pk_state.pot_total_amount() if hasattr(pk_state, 'pot_total_amount') and callable(pk_state.pot_total_amount) else sum(pk_state.pot_contributions()) if hasattr(pk_state, 'pot_contributions') and callable(pk_state.pot_contributions) else 0, # pokerkit 0.7.0
            "game_id": game_id
        }
        
        prompt = format_poker_state_for_llm(game_state_dict, player_index, self.player_name)
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=0.7, # Adjust for desired randomness/creativity
            )
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
            )
            
            raw_response_text = response.text.strip()
            if raw_response_text.startswith("```json"):
                raw_response_text = raw_response_text[7:]
            if raw_response_text.endswith("```"):
                raw_response_text = raw_response_text[:-3]
            
            action_json = json.loads(raw_response_text.strip())
            
            if not isinstance(action_json, dict) or "action_type" not in action_json:
                print(f"Error: Gemini response for {self.player_name} was not a valid action JSON: {action_json}")
                raise ValueError("Invalid JSON response format from LLM.")

            valid_action_types = ["fold", "check", "call", "bet", "raise"]
            if action_json.get("action_type") not in valid_action_types:
                print(f"Error: Gemini response for {self.player_name} had an invalid action_type: {action_json.get('action_type')}")
                raise ValueError("Invalid action_type from LLM.")

            if "amount" in action_json and action_json["amount"] is not None:
                try:
                    action_json["amount"] = int(action_json["amount"])
                except ValueError:
                    print(f"Error: Gemini response for {self.player_name} had a non-integer amount: {action_json['amount']}")
                    raise ValueError("Invalid amount type from LLM, must be integer.")

            return {"action_type": action_json["action_type"], "amount": action_json.get("amount")} 

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Gemini for {self.player_name}: {e}. Response was: {response.text if 'response' in locals() else 'N/A'}")
        except ValueError as e:
            print(f"Validation Error for Gemini response ({self.player_name}): {e}")
        except Exception as e:
            print(f"Error during Gemini API call or processing for {self.player_name}: {e}")
        
        return {"action_type": "fold"} # Simplified fallback

    def _fallback_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Provides a default action (check if possible, otherwise fold) in case of errors."""
        available_actions = game_state.get("available_actions", [])
        checking_or_calling_amount = game_state.get("checking_or_calling_amount", 0)
        if "check_or_call" in available_actions and checking_or_calling_amount == 0:
            print(f"{self.player_name} (fallback): Checking")
            return {"action_type": "check"}
        print(f"{self.player_name} (fallback): Folding")
        return {"action_type": "fold"}

# Example of how to test this class (optional)
if __name__ == '__main__':
    if not GEMINI_API_KEY:
        print("Please set your GEMINI_API_KEY in a .env file in the backend directory to run this test.")
    else:
        print(f"Using Gemini API Key: {GEMINI_API_KEY[:5]}...{GEMINI_API_KEY[-5:]}")
        ai_player_default = GeminiAI(player_name="Test Gemini Player (Default Model)")

        example_game_state_for_ai = {
            "game_id": "test_llm_game_123",
            "variant": "No-Limit Texas Hold'em",
            "initial_bet_size": 1,
            "status": True,
            "actor_index": 0,
            "street_name": "Pre-Flop",
            "hole_cards": [["7S", "8S"], ["TC", "TD"]],
            "community_cards": [],
            "stacks": [98, 98],
            "pot_contributions": [1, 2],
            "pot_total": 3,
            "available_actions": ["fold", "check_or_call", "complete_bet_or_raise_to"],
            "checking_or_calling_amount": 2, 
            "min_raise_to_amount": 4,    
            "max_raise_to_amount": 98, 
            "player_identities": [ai_player_default.player_name, "Opponent"],
            "last_action_details": None
        }

        print(f"\nRequesting action from {ai_player_default.player_name}...")
        action = ai_player_default.get_action(example_game_state_for_ai, 0)
        print(f"Action chosen by {ai_player_default.player_name}: {action}")
