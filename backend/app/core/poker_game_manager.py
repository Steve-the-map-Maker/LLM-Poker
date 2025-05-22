import uuid
from typing import Dict, List, Optional, Tuple

import pokerkit
from pokerkit import NoLimitTexasHoldem, State, Mode

class PokerGameManager:
    """
    Manages active poker game instances using PokerKit.
    Games are stored in-memory.
    """
    def __init__(self, initial_stacks: Optional[List[int]] = None):
        """Initializes the PokerGameManager with an empty dictionary for active games."""
        self.active_games: Dict[str, State] = {}
        self.initial_stacks = initial_stacks if initial_stacks is not None else [20000, 20000]  # Default 200 BBs if BB is 100
        self.default_automations = pokerkit.Automation  # Revert to using pokerkit.Automation to include all available automations.

    def create_game(
        self,
        player_stacks: List[int],
        blinds_tuple: Tuple[int, int],
    ) -> str:
        """
        Creates a new No-Limit Texas Hold'em game instance using integer amounts.

        Args:
            player_stacks: A list of starting chip stacks for each player (as integers).
            blinds_tuple: A tuple containing the small blind and big blind amounts (as integers).

        Returns:
            The unique game ID for the created game.
        """
        game_id = str(uuid.uuid4())
        
        ante = 0
        current_min_bet = blinds_tuple[1]
        player_count = len(player_stacks)

        game_state = NoLimitTexasHoldem.create_state(
            self.default_automations,  # automations
            False,                     # ante_trimming_status (uniform antes)
            ante,                      # raw_antes 
            blinds_tuple,              # raw_blinds_or_straddles
            current_min_bet,           # min_bet
            player_stacks,             # raw_starting_stacks
            player_count,              # player_count
            mode=Mode.CASH_GAME        # mode
        )
        
        self.active_games[game_id] = game_state
        return game_id

    def get_game_state(self, game_id: str) -> Optional[State]:
        """Retrieves the current state of a game by its ID."""
        return self.active_games.get(game_id)

    def update_game_state(self, game_id: str, new_state: State) -> None:
        """Updates the state of an active game."""
        if game_id in self.active_games:
            self.active_games[game_id] = new_state
        else:
            # Or handle as an error, e.g., raise ValueError("Game ID not found")
            print(f"Warning: Game ID {game_id} not found in active_games for update.")
