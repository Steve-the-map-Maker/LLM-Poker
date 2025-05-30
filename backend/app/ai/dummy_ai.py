import pokerkit
from app.ai.base_ai import AIPlayer
from app.api.v1.poker_schemas import PlayerActionRequest # Adjusted import path

class DummyAI(AIPlayer):
    async def get_action(self, pk_state: pokerkit.State, player_index: int, game_id: str, player_name: str) -> PlayerActionRequest:
        print(f"DummyAI ({player_name}, index {player_index}) is thinking for game {game_id}...")
        
        # Simple logic: always call/check if possible, otherwise fold.
        if pk_state.can_check_or_call():
            amount_to_call = pk_state.checking_or_calling_amount
            print(f"DummyAI chooses: check_or_call (amount: {amount_to_call})")
            return PlayerActionRequest(action_type="check_or_call", amount=amount_to_call if amount_to_call > 0 else None)
        elif pk_state.can_fold():
            print(f"DummyAI chooses: fold")
            return PlayerActionRequest(action_type="fold")
        else:
            # This case should ideally not be reached if it's the player's turn and the game is not over.
            # It implies no valid actions are available, which might indicate an issue or a specific game end scenario.
            print(f"DummyAI has no valid actions (e.g., must be all-in or game ended unexpectedly). Folding as a fallback.")
            return PlayerActionRequest(action_type="fold")
