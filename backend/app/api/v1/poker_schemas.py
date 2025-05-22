from pydantic import BaseModel
from typing import Optional, List, Any, Dict  # Added Dict

class PlayerActionRequest(BaseModel):
    player_id: Optional[str] = None  # For human player identification
    action_type: str  # "fold", "call", "check", "raise"
    amount: Optional[int] = None  # Total amount for a raise action

class StartGameRequest(BaseModel):
    player_one_ai_type: str
    player_two_ai_type: str
    human_player_index: Optional[int] = None
    initial_stacks: Optional[List[int]] = [10000, 10000] # Default stacks
    blinds: Optional[List[int]] = [50,100] # Default blinds

class GameStateResponse(BaseModel):
    game_id: str
    status: bool # True if game is ongoing, False if hand/game is over
    player_count: int
    button_index: int
    actor_index: Optional[int]
    stacks: List[int]
    bets: List[int]
    pot_total: int # Calculated from bets
    board_cards: List[str]
    player_hole_cards: Optional[Dict[int, List[str]]] = None # Keyed by player_index
    payoffs: Optional[List[int]] = None
    available_actions: Optional[List[str]] = None # e.g. ["fold", "check_or_call", "complete_bet_or_raise_to"]
    checking_or_calling_amount: Optional[int] = None
    min_raise_to_amount: Optional[int] = None
    max_raise_to_amount: Optional[int] = None
    current_round_name: Optional[str] = None # e.g. "PREFLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"
    last_action_details: Optional[Dict[str, Any]] = None # Details of the last action taken
    error_message: Optional[str] = None
