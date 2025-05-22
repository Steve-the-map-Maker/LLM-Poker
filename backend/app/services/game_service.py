from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from pokerkit import State # Removed BlindOrStraddlePosting

from backend.app.core.poker_game_manager import PokerGameManager
from backend.app.api.v1.poker_schemas import GameStateResponse, PlayerActionRequest, StartGameRequest

class GameService:
    """
    Service layer for managing poker game logic.
    It interfaces with PokerGameManager and handles data transformation for API responses.
    """
    def __init__(self, game_manager: PokerGameManager):
        self.game_manager = game_manager

    def _pokerkit_state_to_api_response(
        self, game_id: str, pk_state: State, human_player_index: Optional[int] = None
    ) -> GameStateResponse:
        """
        Transforms a PokerKit State object into a GameStateResponse Pydantic model.
        """
        # Ensure pk_state.board_cards is accessed correctly, assuming it's list[list[Card]]
        # For simplicity, taking the first board if multiple exist, or empty if none.
        current_board_cards = []
        if pk_state.board_cards and pk_state.board_cards[0]:
            current_board_cards = [str(card) for card in pk_state.board_cards[0]]
        elif pk_state.board_cards: # It exists but the first board is empty (e.g. setup for multi-board)
            current_board_cards = []
        
        player_hole_cards: Dict[int, List[str]] = {} # Initialize as empty dict
        if pk_state.status is False: # Hand is over, reveal all cards
            for i in range(pk_state.player_count):
                # Access hole_cards directly as it's a list of lists
                if 0 <= i < len(pk_state.hole_cards):
                    hole_cards_for_player_i = pk_state.hole_cards[i]
                    if hole_cards_for_player_i:  # Check if the list is not empty
                        player_hole_cards[i] = [str(card) for card in hole_cards_for_player_i]
        elif human_player_index is not None and pk_state.actor_index == human_player_index:
            if 0 <= human_player_index < len(pk_state.hole_cards): # Check bounds
                human_cards_for_player = pk_state.hole_cards[human_player_index] # Access hole_cards directly
                if human_cards_for_player:  # Check if the list is not empty
                    player_hole_cards[human_player_index] = [str(card) for card in human_cards_for_player]
        
        # Determine current round name
        current_round_name = "PRE_FLOP" # Default
        if pk_state.status is False: # Hand is over
            if pk_state.showdown_indices: # Check if players are in the showdown queue
                current_round_name = "SHOWDOWN"
            else:
                current_round_name = "HAND_OVER" # Ended before or without a formal showdown sequence
        # If hand is ongoing (pk_state.status is True)
        elif pk_state.board_cards and pk_state.board_cards[0]: # Check if board_cards and the first board are not empty
            num_board_cards = len(pk_state.board_cards[0])
            if num_board_cards == 5:
                current_round_name = "RIVER"
            elif num_board_cards == 4:
                current_round_name = "TURN"
            elif num_board_cards == 3:
                current_round_name = "FLOP"
        elif not pk_state.board_cards: # No boards initialized yet, or no cards on any board.
             current_round_name = "PRE_FLOP"
        # else it remains PRE_FLOP (e.g. board_cards exists but board_cards[0] is empty)

        determined_button_index = 0 # As per existing logic/comment

        available_actions = []
        checking_or_calling_amount = None
        min_raise_to_amount = None
        max_raise_to_amount = None

        if pk_state.status and pk_state.actor_index is not None: #
            if pk_state.can_fold(): #
                available_actions.append("fold")
            if pk_state.can_check_or_call(): #
                available_actions.append("check_or_call")
                checking_or_calling_amount = pk_state.checking_or_calling_amount #
            if pk_state.can_complete_bet_or_raise_to(): # Checks if any raise is possible
                available_actions.append("complete_bet_or_raise_to")
                min_raise_to_amount = pk_state.min_completion_betting_or_raising_to_amount #
                max_raise_to_amount = pk_state.max_completion_betting_or_raising_to_amount #

        return GameStateResponse(
            game_id=game_id,
            status=pk_state.status, #
            player_count=pk_state.player_count, #
            button_index=determined_button_index,
            actor_index=pk_state.actor_index, #
            stacks=[int(s) for s in pk_state.stacks], #
            bets=[int(b) for b in pk_state.bets], #
            pot_total=pk_state.total_pot_amount, # Use total_pot_amount property
            board_cards=current_board_cards, # Use the processed board cards
            player_hole_cards=player_hole_cards,
            payoffs=[int(p) for p in pk_state.payoffs] if pk_state.payoffs is not None else None, #
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
        """
        player_stacks = start_game_request.initial_stacks if start_game_request.initial_stacks else [10000, 10000]
        raw_blinds = start_game_request.blinds if start_game_request.blinds else [50, 100]
        blinds: Tuple[int, int] = (raw_blinds[0], raw_blinds[1])

        game_id = self.game_manager.create_game(player_stacks, blinds)
        pk_state = self.game_manager.get_game_state(game_id)
        if not pk_state:
            # This case should ideally not happen if create_game is successful
            raise Exception("Failed to create or retrieve game state immediately after creation.")

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
        """
        pk_state = self.game_manager.get_game_state(game_id)
        if not pk_state:
            # Consider returning a specific error response or raising an exception
            return GameStateResponse(game_id=game_id, status=False, error_message="Game not found", player_count=0, button_index=0, actor_index=None, stacks=[], bets=[], pot_total=0, board_cards=[])

        # Check if it's the player's turn before processing action
        if pk_state.actor_index != human_player_index: #
            # It's not this player's turn, return current state with an error message
            response = self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
            response.error_message = f"Not player {human_player_index}'s turn. Current actor is {pk_state.actor_index}."
            return response
        
        action_taken_details = {"player_index": human_player_index, "action": action_request.action_type}

        try:
            if action_request.action_type == "fold":
                if pk_state.can_fold(): #
                    pk_state.fold() #
                else:
                    raise ValueError("Cannot fold at this time.")
            elif action_request.action_type == "check_or_call":
                if pk_state.can_check_or_call(): #
                    action_taken_details["amount"] = pk_state.checking_or_calling_amount # Capture amount before action
                    pk_state.check_or_call() #
                else:
                    raise ValueError("Cannot check or call at this time.")
            elif action_request.action_type == "raise" or action_request.action_type == "bet": # 'bet' is often synonymous with 'raise' to an opening amount
                if action_request.amount is None:
                    raise ValueError("Amount must be provided for a raise/bet action.")
                # PokerKit uses complete_bet_or_raise_to for both betting and raising
                if pk_state.can_complete_bet_or_raise_to(action_request.amount): #
                    pk_state.complete_bet_or_raise_to(action_request.amount) #
                    action_taken_details["amount"] = action_request.amount
                else:
                    min_raise = pk_state.min_completion_betting_or_raising_to_amount #
                    max_raise = pk_state.max_completion_betting_or_raising_to_amount #
                    raise ValueError(f"Invalid raise amount. Min: {min_raise}, Max: {max_raise}, Got: {action_request.amount}")
            else:
                raise ValueError(f"Unknown action type: {action_request.action_type}")
            
        except ValueError as e:
            # If an action fails, return the current state with an error message
            response = self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
            response.error_message = str(e)
            # response.last_action_details = None # Clearing this as the action failed
            return response

        # If action is successful, return the new state
        response = self._pokerkit_state_to_api_response(game_id, pk_state, human_player_index)
        response.last_action_details = action_taken_details # Add details of the successful action
        return response

    def run_ai_vs_ai_game_turn(self, game_id: str) -> GameStateResponse:
        # This method seems designed for a scenario where AI plays.
        # For now, it just returns the current state.
        # Further logic would be needed here to make an AI move.
        pk_state = self.game_manager.get_game_state(game_id)
        if not pk_state:
            return GameStateResponse(game_id=game_id, status=False, error_message="Game not found", player_count=0, button_index=0, actor_index=None, stacks=[], bets=[], pot_total=0, board_cards=[])

        # Typically, you'd want some AI logic here to choose and perform an action
        # For example:
        # if pk_state.status and pk_state.actor_index is not None:
        #     ai_player_index = pk_state.actor_index
        #     # Simple AI: always check or call if possible, else fold
        #     if pk_state.can_check_or_call():
        #         pk_state.check_or_call()
        #     elif pk_state.can_fold():
        #         pk_state.fold()
        #     # else: AI is stuck or hand ended

        return self._pokerkit_state_to_api_response(game_id, pk_state)