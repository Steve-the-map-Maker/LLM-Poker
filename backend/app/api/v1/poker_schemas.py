from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any, Dict
import re

class PlayerActionRequest(BaseModel):
    player_id: Optional[str] = None  # For human player identification
    action_type: str = Field(..., pattern="^(fold|call|check|raise|bet)$")  # Validate action types
    amount: Optional[int] = Field(None, ge=0)  # Amount must be >= 0 if provided
    reasoning: Optional[str] = Field(None, max_length=500)  # AI's raw response/trash talk for chat

class PlayerConfig(BaseModel):
    name: Optional[str] = Field(None, max_length=50)  # Limit name length
    ai_type: str = Field(..., pattern="^(human|gemini|gpt|claude|dummy)$")  # Validate AI types
    stack: Optional[int] = Field(None, ge=100, le=10000000)  # Stack between 100 and 10M
    persona: Optional[str] = Field(None, pattern="^(default|conservative|aggressive|calling_station)$")
    gemini_model: Optional[str] = Field(None, max_length=100)
    claude_model: Optional[str] = Field(None, max_length=100)
    gpt_model: Optional[str] = Field(None, max_length=100)
    custom_prompt: Optional[str] = Field(None, max_length=500)  # Custom AI personality/strategy
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v):
        if v is not None:
            # Remove any HTML/script tags for XSS prevention
            v = re.sub(r'<[^>]+>', '', v)
            v = v.strip()
        return v

class StartGameRequest(BaseModel):
    # Deprecated fields (kept for backward compatibility lightly, or optional)
    player_one_ai_type: Optional[str] = None 
    player_two_ai_type: Optional[str] = None
    
    # New Field
    players: Optional[List[PlayerConfig]] = Field(None, max_length=6)  # Max 6 players
    
    human_player_index: Optional[int] = Field(None, ge=0, le=5)  # Valid player indices
    initial_stacks: Optional[List[int]] = Field([10000, 10000], max_length=6)
    blinds: Optional[List[int]] = Field([50, 100], max_length=2)
    
    @field_validator('blinds')
    @classmethod
    def validate_blinds(cls, v):
        if v and len(v) >= 2:
            if v[0] <= 0 or v[1] <= 0:
                raise ValueError('Blinds must be positive values')
            if v[0] >= v[1]:
                raise ValueError('Small blind must be less than big blind')
        return v
    
    @field_validator('players')
    @classmethod
    def validate_player_count(cls, v):
        if v and len(v) < 2:
            raise ValueError('Minimum 2 players required')
        return v

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
    player_names: Optional[List[str]] = None  # Actual player names from game setup
    players_folded: Optional[List[bool]] = None  # True if player has folded
    payoffs: Optional[List[int]] = None
    available_actions: Optional[List[str]] = None # e.g. ["fold", "check_or_call", "complete_bet_or_raise_to"]
    checking_or_calling_amount: Optional[int] = None
    min_raise_to_amount: Optional[int] = None
    max_raise_to_amount: Optional[int] = None
    current_round_name: Optional[str] = None # e.g. "PREFLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"
    last_action_details: Optional[Dict[str, Any]] = None # Details of the last action taken
    error_message: Optional[str] = None
    ai_message: Optional[str] = None  # AI thought/reasoning for chat panel
    # Showdown data
    winning_player_index: Optional[int] = None  # Index of the winning player
    winning_hand_name: Optional[str] = None  # e.g., "Flush, Ace high"
    winning_cards: Optional[List[str]] = None  # The 5-card winning combination

