import uuid
from typing import Dict, List, Optional, Tuple

from pokerkit import NoLimitTexasHoldem, State, Automation, Mode

class PokerGameManager:
    """
    Manages active poker game instances using PokerKit.
    Games are stored in-memory.
    """
    def __init__(self):
        """Initializes the PokerGameManager with an empty dictionary for active games."""
        self.active_games: Dict[str, State] = {}

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

        # Default automations as per PokerKit best practices/examples
        default_automations = (
            Automation.ANTE_POSTING,
            Automation.BET_COLLECTION,
            Automation.BLIND_OR_STRADDLE_POSTING,
            Automation.HOLE_DEALING,  # Added HOLE_DEALING
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            Automation.HAND_KILLING,
            Automation.CHIPS_PUSHING,
            Automation.CHIPS_PULLING,
        )

        game_state = NoLimitTexasHoldem.create_state(
            default_automations,  # automations
            False,                # ante_trimming_status (uniform antes)
            ante,                 # raw_antes 
            blinds_tuple,         # raw_blinds_or_straddles
            current_min_bet,      # min_bet
            player_stacks,        # raw_starting_stacks
            player_count,         # player_count
            mode=Mode.CASH_GAME   # mode
        )
        
        self.active_games[game_id] = game_state
        return game_id

    def get_game_state(self, game_id: str) -> Optional[State]:
        """Retrieves the current state of a game by its ID."""
        return self.active_games.get(game_id)
