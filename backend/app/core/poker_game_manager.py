import uuid
import time
from typing import Dict, List, Optional, Tuple

import pokerkit
from pokerkit import NoLimitTexasHoldem, State, Mode

class PokerGameManager:
    """
    Manages active poker game instances using PokerKit.
    Games are stored in-memory with expiration tracking.
    """
    # Game expiration time in seconds (30 minutes)
    GAME_EXPIRATION_SECONDS = 30 * 60
    
    def __init__(self, initial_stacks: Optional[List[int]] = None):
        """Initializes the PokerGameManager with an empty dictionary for active games."""
        self.active_games: Dict[str, State] = {}
        self.game_created_at: Dict[str, float] = {}  # Track creation time for expiration
        self.game_last_activity: Dict[str, float] = {}  # Track last activity time
        self.initial_stacks = initial_stacks if initial_stacks is not None else [20000, 20000]
        
        # Explicitly define automations to ensure smooth game flow
        # RUNOUT_COUNT_SELECTION is required for all-in scenarios to complete automatically
        self.default_automations = [
            pokerkit.Automation.ANTE_POSTING,
            pokerkit.Automation.BET_COLLECTION,
            pokerkit.Automation.BLIND_OR_STRADDLE_POSTING,
            pokerkit.Automation.HOLE_DEALING,
            pokerkit.Automation.BOARD_DEALING,
            pokerkit.Automation.RUNOUT_COUNT_SELECTION,  # Required for all-in completion
            pokerkit.Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            pokerkit.Automation.HAND_KILLING,
            pokerkit.Automation.CHIPS_PUSHING,
            pokerkit.Automation.CHIPS_PULLING,
            pokerkit.Automation.CARD_BURNING,
        ]

    def create_game(
        self,
        player_stacks: List[int],
        blinds_tuple: Tuple[int, int],
        game_id_override: Optional[str] = None,
        button_index: Optional[int] = None
    ) -> str:
        """
        Creates a new No-Limit Texas Hold'em game instance using integer amounts.

        Args:
            player_stacks: A list of starting chip stacks for each player (as integers).
            blinds_tuple: A tuple containing the small blind and big blind amounts (as integers).
            game_id_override: Optional ID to use (for restarting a hand in the same game).
            button_index: Optional index to set the dealer button.

        Returns:
            The unique game ID for the created game.
        """
        # Clean up expired games before creating new ones
        self.cleanup_expired_games()
        
        game_id = game_id_override if game_id_override else str(uuid.uuid4())
        
        ante = 0
        current_min_bet = blinds_tuple[1]
        player_count = len(player_stacks)
        
        game_state = NoLimitTexasHoldem.create_state(
            self.default_automations,  # automations list
            False,                     # ante_trimming_status
            ante,                      # raw_antes 
            blinds_tuple,              # raw_blinds_or_straddles
            current_min_bet,           # min_bet
            player_stacks,             # raw_starting_stacks
            player_count,              # player_count
            mode=Mode.CASH_GAME        # mode
        )
        
        if button_index is not None:
            game_state.button_index = button_index
        
        current_time = time.time()
        self.active_games[game_id] = game_state
        self.game_created_at[game_id] = current_time
        self.game_last_activity[game_id] = current_time
        
        return game_id

    def get_game_state(self, game_id: str) -> Optional[State]:
        """Retrieves the current state of a game by its ID."""
        if game_id in self.active_games:
            # Update last activity time
            self.game_last_activity[game_id] = time.time()
        return self.active_games.get(game_id)

    def update_game_state(self, game_id: str, new_state: State) -> None:
        """Updates the state of an active game."""
        if game_id in self.active_games:
            self.active_games[game_id] = new_state
            self.game_last_activity[game_id] = time.time()
        else:
            print(f"Warning: Game ID {game_id} not found in active_games for update.")
    
    def cleanup_expired_games(self) -> int:
        """
        Removes games that have been inactive for longer than GAME_EXPIRATION_SECONDS.
        
        Returns:
            Number of games removed.
        """
        current_time = time.time()
        expired_games = []
        
        for game_id, last_activity in self.game_last_activity.items():
            if current_time - last_activity > self.GAME_EXPIRATION_SECONDS:
                expired_games.append(game_id)
        
        for game_id in expired_games:
            self.remove_game(game_id)
            print(f"Cleaned up expired game: {game_id}")
        
        return len(expired_games)
    
    def remove_game(self, game_id: str) -> bool:
        """
        Removes a game from the manager.
        
        Returns:
            True if game was found and removed, False otherwise.
        """
        if game_id in self.active_games:
            del self.active_games[game_id]
            self.game_created_at.pop(game_id, None)
            self.game_last_activity.pop(game_id, None)
            return True
        return False
    
    def get_active_game_count(self) -> int:
        """Returns the number of currently active games."""
        return len(self.active_games)
    
    def get_game_stats(self) -> Dict:
        """Returns statistics about active games."""
        current_time = time.time()
        oldest_age = 0
        if self.game_created_at:
            oldest_age = current_time - min(self.game_created_at.values())
        
        return {
            "active_games": len(self.active_games),
            "oldest_game_age_seconds": oldest_age,
        }

