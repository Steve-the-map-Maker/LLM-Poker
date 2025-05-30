import unittest
import uuid

from pokerkit import State

from app.core.poker_game_manager import PokerGameManager

class TestPokerGameManager(unittest.TestCase):
    def setUp(self):
        """Set up for test methods."""
        self.manager = PokerGameManager()
        self.player_stacks = [10000, 10000]
        self.blinds = (50, 100)

    def test_create_game(self):
        """Test creating a new game."""
        game_id = self.manager.create_game(self.player_stacks, self.blinds)
        self.assertIsNotNone(game_id)
        self.assertIsInstance(game_id, str)
        
        # Check if the game_id is a valid UUID string
        try:
            uuid.UUID(game_id)
        except ValueError:
            self.fail("game_id is not a valid UUID string")

        self.assertIn(game_id, self.manager.active_games)
        game_state = self.manager.active_games[game_id]
        self.assertIsInstance(game_state, State)
        self.assertEqual(game_state.player_count, len(self.player_stacks))
        
        # Player 0 (dealer) posts Big Blind, Player 1 posts Small Blind in PokerKit heads-up.
        # Blinds are (SB, BB) -> (self.blinds[0], self.blinds[1])
        # Player 0 stack: initial_stack - BB (self.blinds[1])
        # Player 1 stack: initial_stack - SB (self.blinds[0])
        expected_stacks_after_blinds = [
            self.player_stacks[0] - self.blinds[1],
            self.player_stacks[1] - self.blinds[0]
        ]
        self.assertEqual([int(s) for s in game_state.stacks], expected_stacks_after_blinds)
        self.assertEqual(game_state.blinds_or_straddles, self.blinds)

        # Player 0 is Button/BB, Player 1 is SB. SB (Player 1) acts first pre-flop.
        expected_actor_index = 1
        self.assertEqual(game_state.actor_index, expected_actor_index)

        # Verify board and hand cards (should be empty or dealt depending on automations)

    def test_get_game_state_existing_game(self):
        """Test retrieving an existing game state."""
        game_id = self.manager.create_game(self.player_stacks, self.blinds)
        retrieved_state = self.manager.get_game_state(game_id)
        self.assertIsNotNone(retrieved_state)
        self.assertIsInstance(retrieved_state, State)
        self.assertEqual(retrieved_state, self.manager.active_games[game_id])

    def test_get_game_state_non_existing_game(self):
        """Test retrieving a non-existing game state."""
        non_existent_game_id = str(uuid.uuid4())
        retrieved_state = self.manager.get_game_state(non_existent_game_id)
        self.assertIsNone(retrieved_state)

if __name__ == '__main__':
    unittest.main()
