from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from pokerkit import State
from backend.app.core.poker_game_manager import PokerGameManager
from backend.app.api.v1.poker_schemas import GameStateResponse, PlayerActionRequest, StartGameRequest
from backend.app.ai.base_ai import AIPlayer
from backend.app.ai.dummy_ai import DummyAI

class GameService:
    """
    Service layer for managing poker game logic.
    It interfaces with PokerGameManager and handles data transformation for API responses.
    """
    def __init__(self, game_manager: PokerGameManager):
        self.game_manager = game_manager
        self.game_player_identities: Dict[str, Dict[int, str]] = {}  # Stores AI type or "human" for each player_index in a game
        self.ai_constructors: Dict[str, type[AIPlayer]] = {
            "dummy": DummyAI
        }

    def _get_ai_instance(self, ai_type: str) -> AIPlayer:
        """Helper method to instantiate an AI player based on its type."""
        constructor = self.ai_constructors.get(ai_type.lower())
        if not constructor:
            raise ValueError(f"Unknown AI type: {ai_type}")
        return constructor()

    def _pokerkit_state_to_api_response(
        self, game_id: str, pk_state: State, human_player_index: Optional[int] = None
    ) -> GameStateResponse:
        """
        Transforms a PokerKit State object into a GameStateResponse Pydantic model.
        """
        current_board_cards = []
        if pk_state.board_cards:
            current_board_cards = [str(card) for card in pk_state.board_cards]
        
        player_hole_cards: Dict[int, List[str]] = {}
        # DEBUG: Always show all hole cards
        for i in range(pk_state.player_count):
            if 0 <= i < len(pk_state.hole_cards):
                hole_cards_for_player_i = pk_state.hole_cards[i]
                if hole_cards_for_player_i:
                    player_hole_cards[i] = [str(card) for card in hole_cards_for_player_i]

        current_round_name = "PRE_FLOP"
        if pk_state.status is False:
            if pk_state.showdown_indices:
                current_round_name = "SHOWDOWN"
            else:
                current_round_name = "HAND_OVER"
        elif pk_state.board_cards:
            num_board_cards = len(pk_state.board_cards)
            if num_board_cards == 5:
                current_round_name = "RIVER"
            elif num_board_cards == 4:
                current_round_name = "TURN"
            elif num_board_cards == 3:
                current_round_name = "FLOP"
        else:
             current_round_name = "PRE_FLOP"

        determined_button_index = 0

        available_actions = []
        checking_or_calling_amount = None
        min_raise_to_amount = None
        max_raise_to_amount = None

        if pk_state.status and pk_state.actor_index is not None:
            if pk_state.can_fold():
                available_actions.append("fold")
            if pk_state.can_check_or_call():
                available_actions.append("check_or_call")
                checking_or_calling_amount = pk_state.checking_or_calling_amount
            if pk_state.can_complete_bet_or_raise_to():
                available_actions.append("complete_bet_or_raise_to")
                min_raise_to_amount = pk_state.min_completion_betting_or_raising_to_amount
                max_raise_to_amount = pk_state.max_completion_betting_or_raising_to_amount

        return GameStateResponse(
            game_id=game_id,
            status=pk_state.status,
            player_count=pk_state.player_count,
            button_index=determined_button_index,
            actor_index=pk_state.actor_index,
            stacks=[int(s) for s in pk_state.stacks],
            bets=[int(b) for b in pk_state.bets],
            pot_total=pk_state.total_pot_amount,
            board_cards=current_board_cards,
            player_hole_cards=player_hole_cards,
            payoffs=[int(p) for p in pk_state.payoffs] if pk_state.payoffs is not None else None,
            available_actions=available_actions,
            checking_or_calling_amount=checking_or_calling_amount,
            min_raise_to_amount=min_raise_to_amount,
            max_raise_to_amount=max_raise_to_amount,
            current_round_name=current_round_name,
        )

    def create_new_game_instance(
        self, start_game_request: StartGameRequest
    ) -> GameStateResponse:
        """
        Creates a new game instance and returns its initial state.
        Stores player identities (human/AI type).
        """
        player_stacks = start_game_request.initial_stacks if start_game_request.initial_stacks else [10000, 10000]
        raw_blinds = start_game_request.blinds if start_game_request.blinds else [50, 100]
        blinds: Tuple[int, int] = (raw_blinds[0], raw_blinds[1])

        game_id = self.game_manager.create_game(player_stacks, blinds)
        pk_state = self.game_manager.get_game_state(game_id)
        if not pk_state:
            raise Exception("Failed to create or retrieve game state immediately after creation.")

        self.game_player_identities[game_id] = {}
        if start_game_request.human_player_index == 0:
            self.game_player_identities[game_id][0] = "human"
        else:
            self.game_player_identities[game_id][0] = start_game_request.player_one_ai_type or "dummy"
        
        if start_game_request.human_player_index == 1:
            self.game_player_identities[game_id][1] = "human"
        else:
            self.game_player_identities[game_id][1] = start_game_request.player_two_ai_type or "dummy"
        
        print(f"Game {game_id} player identities: {self.game_player_identities[game_id]}")

        human_player_index = start_game_request.human_player_index
        return self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)

    def get_game_state(self, game_id: str, human_player_index: Optional[int] = None) -> Optional[GameStateResponse]:
        """
        Retrieves the current state of a game.
        """
        pk_state = self.game_manager.get_game_state(game_id)
        if pk_state:
            return self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
        return None

    def process_human_action(
        self, game_id: str, action_request: PlayerActionRequest, human_player_index: int
    ) -> GameStateResponse:
        """
        Processes an action from a human player.
        Validates the action and updates the PokerKit state.
        The human_player_index is now confirmed by the API endpoint before calling this.
        """
        pk_state = self.game_manager.get_game_state(game_id)
        # Create a default error response shell, to be populated if issues arise early
        default_error_response_shell = GameStateResponse(
            game_id=game_id, status=False, player_count=0, button_index=0, 
            actor_index=None, stacks=[], bets=[], pot_total=0, board_cards=[]
        )

        if not pk_state:
            default_error_response_shell.error_message = "Game not found"
            return default_error_response_shell

        if pk_state.actor_index != human_player_index:
            response = self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
            response.error_message = f"Not player {human_player_index}'s turn. Current actor is {pk_state.actor_index}."
            return response
        
        action_taken_details = {"player_index": human_player_index, "action_type": action_request.action_type} # Renamed "action" to "action_type" for consistency

        try:
            action_type_lower = action_request.action_type.lower()

            if action_type_lower == "fold":
                if pk_state.can_fold():
                    pk_state.fold()
                else:
                    raise ValueError("Cannot fold at this time.")
            elif action_type_lower == "check" or action_type_lower == "call": # Frontend might send "check" or "call" separately
                if pk_state.can_check_or_call():
                    action_taken_details["amount_called"] = pk_state.checking_or_calling_amount
                    pk_state.check_or_call()
                else:
                    raise ValueError("Cannot check or call at this time.")
            # Frontend sends "bet" for initial bet in a round, "raise" for subsequent raises.
            # PokerKit uses complete_bet_or_raise_to for both.
            elif action_type_lower == "raise" or action_type_lower == "bet": 
                if action_request.amount is None:
                    raise ValueError("Amount must be provided for a bet/raise action.")
                
                # Ensure the action is valid with the provided amount
                if pk_state.can_complete_bet_or_raise_to(action_request.amount):
                    pk_state.complete_bet_or_raise_to(action_request.amount)
                    action_taken_details["amount_raised_to"] = action_request.amount
                else:
                    min_bet_raise = pk_state.min_completion_betting_or_raising_to_amount
                    max_bet_raise = pk_state.max_completion_betting_or_raising_to_amount
                    current_bet_to_call = pk_state.checking_or_calling_amount
                    error_detail = f"Invalid bet/raise amount: {action_request.amount}. Current bet to call: {current_bet_to_call}. Min total: {min_bet_raise}, Max total: {max_bet_raise}."
                    # Add more context if it's a bet (no prior bet to call)
                    if current_bet_to_call == 0:
                        error_detail = f"Invalid bet amount: {action_request.amount}. Min bet: {min_bet_raise}, Max bet: {max_bet_raise}."
                    raise ValueError(error_detail)
            else:
                raise ValueError(f"Unknown action type: {action_request.action_type}")
            
        except ValueError as e:
            response = self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
            response.error_message = str(e)
            return response

        # If action was successful, update the game state and last action details
        self.game_manager.update_game_state(game_id, pk_state) # Persist the change
        response = self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
        response.last_action_details = action_taken_details
        return response

    async def run_ai_vs_ai_game_turn(self, game_id: str) -> GameStateResponse:
        """
        Runs a single turn for an AI player if it's their turn.
        Retrieves game state, determines AI actor, gets action, applies action, returns new state.
        """
        pk_state = self.game_manager.get_game_state(game_id)
        if not pk_state:
            return GameStateResponse(game_id=game_id, status=False, error_message="Game not found", player_count=0, button_index=0, actor_index=None, stacks=[], bets=[], pot_total=0, board_cards=[])

        if not pk_state.status:
            print(f"Game {game_id} is over. No AI turn to run.")
            return self._pokerkit_state_to_api_response(game_id, pk_state)

        current_player_index = pk_state.actor_index
        if current_player_index is None:
            print(f"Game {game_id} has no current actor. Hand might be over or in an unexpected state.")
            return self._pokerkit_state_to_api_response(game_id, pk_state)

        player_identities_for_game = self.game_player_identities.get(game_id)
        if not player_identities_for_game:
            error_msg = f"Player identities not found for game {game_id}."
            print(error_msg)
            response = self._pokerkit_state_to_api_response(game_id, pk_state)
            response.error_message = error_msg
            return response
            
        player_name_or_type = player_identities_for_game.get(current_player_index)

        if player_name_or_type is None or player_name_or_type.lower() == "human":
            print(f"Game {game_id}: It's player {current_player_index}'s turn, who is '{player_name_or_type}'. Not an AI turn to run via this method.")
            return self._pokerkit_state_to_api_response(game_id, pk_state)

        print(f"Game {game_id}: AI player {current_player_index} ({player_name_or_type}) is to act.")
        ai_action_request: Optional[PlayerActionRequest] = None
        action_taken_details = {"player_index": current_player_index}

        try:
            ai_player = self._get_ai_instance(player_name_or_type)
            ai_action_request = await ai_player.get_action(pk_state, current_player_index, game_id, player_name_or_type)
            
            action_taken_details["action"] = ai_action_request.action_type
            if ai_action_request.amount is not None:
                 action_taken_details["amount"] = ai_action_request.amount

            print(f"Game {game_id}: AI {player_name_or_type} (P{current_player_index}) requested action: {ai_action_request.action_type}, amount: {ai_action_request.amount}")

            if ai_action_request.action_type == "fold":
                if pk_state.can_fold():
                    pk_state.fold()
                else:
                    raise ValueError("AI requested fold when not possible.")
            elif ai_action_request.action_type == "check_or_call":
                if pk_state.can_check_or_call():
                    pk_state.check_or_call()
                else:
                    raise ValueError("AI requested check/call when not possible.")
            elif ai_action_request.action_type in ["raise", "bet", "complete_bet_or_raise_to"]:
                required_amount = ai_action_request.amount
                if required_amount is None and ai_action_request.action_type in ["raise", "bet"]:
                    raise ValueError("AI requested raise/bet without specifying an amount.")

                if pk_state.can_complete_bet_or_raise_to(required_amount):
                    pk_state.complete_bet_or_raise_to(required_amount)
                else:
                    min_r = pk_state.min_completion_betting_or_raising_to_amount
                    max_r = pk_state.max_completion_betting_or_raising_to_amount
                    raise ValueError(f"AI requested invalid raise. Amount: {required_amount}. Valid range: [{min_r}-{max_r}]")
            else:
                raise ValueError(f"AI provided unknown action type: {ai_action_request.action_type}")

        except ValueError as e:
            print(f"Error processing AI action for game {game_id}, player {current_player_index} ({player_name_or_type}): {e}. AI will attempt to fold.")
            if pk_state.can_fold():
                pk_state.fold()
                action_taken_details["action"] = "fold"
                action_taken_details["amount"] = None
                action_taken_details["original_error"] = str(e)
            else:
                print(f"AI could not perform original action due to error '{e}', and also cannot fold. Game state may be unchanged or hand ended.")
                response = self._pokerkit_state_to_api_response(game_id, pk_state, None)
                response.error_message = f"AI Error: {e}. Fallback fold also not possible."
                response.last_action_details = None
                return response
        
        except Exception as e:
            print(f"Unexpected error from AI {player_name_or_type} (P{current_player_index}) for game {game_id}: {e}. AI will attempt to fold.")
            if pk_state.can_fold():
                pk_state.fold()
                action_taken_details["action"] = "fold"
                action_taken_details["amount"] = None
                action_taken_details["original_error"] = str(e)
            else:
                print(f"AI had unexpected error '{e}', and also cannot fold.")
                response = self._pokerkit_state_to_api_response(game_id, pk_state, None)
                response.error_message = f"AI Unexpected Error: {e}. Fallback fold also not possible."
                response.last_action_details = None
                return response

        response = self._pokerkit_state_to_api_response(game_id, pk_state, None)
        response.last_action_details = action_taken_details
        
        # Log betting round status
        if pk_state:
            print(f"Game {game_id}: Board cards after AI action: {pk_state.board_cards}")
            print(f"Game {game_id}: Next to act after AI turn processing: {pk_state.actor_index}")

        print(f"Game {game_id}: AI turn processed. Final actor_index for this call: {pk_state.actor_index}, Status: {pk_state.status}")
        return response