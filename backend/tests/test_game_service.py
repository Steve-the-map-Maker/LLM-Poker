import unittest
from unittest.mock import MagicMock, patch
import uuid

from pokerkit import State, NoLimitTexasHoldem, Automation

from backend.app.core.poker_game_manager import PokerGameManager
from backend.app.services.game_service import GameService
from backend.app.api.v1.poker_schemas import StartGameRequest, PlayerActionRequest, GameStateResponse

class TestGameService(unittest.TestCase):
    def setUp(self):
        """Set up for test methods."""
        self.manager = PokerGameManager() # Use a real manager for some tests
        self.game_service = GameService(game_manager=self.manager)
        
        self.player_stacks = [10000, 10000]
        self.blinds = (50, 100)
        self.start_game_request = StartGameRequest(
            player_one_ai_type="dummy", 
            player_two_ai_type="dummy",
            initial_stacks=self.player_stacks,
            blinds=[self.blinds[0], self.blinds[1]]
        )

    def test_create_new_game_instance(self):
        """Test creating a new game instance via the service."""
        game_state_response = self.game_service.create_new_game_instance(self.start_game_request)
        self.assertIsNotNone(game_state_response)
        self.assertIsInstance(game_state_response, GameStateResponse)
        self.assertEqual(game_state_response.player_count, 2)
        
        # PokerKit default heads-up: Player 0 (dealer) posts BB, Player 1 posts SB.
        # Initial stacks: [10000, 10000]. Blinds: (SB=50, BB=100)
        expected_stacks_after_blinds = [
            self.player_stacks[0] - self.blinds[1],  # P0 pays BB: 10000 - 100 = 9900
            self.player_stacks[1] - self.blinds[0]   # P1 pays SB: 10000 - 50 = 9950
        ]
        self.assertEqual(game_state_response.stacks, expected_stacks_after_blinds)
        self.assertEqual(game_state_response.button_index, 0) # Player 0 is dealer/button
        # After blinds and hole dealing, SB (Player 1) is the first to act in heads-up pre-flop.
        self.assertEqual(game_state_response.actor_index, 1) 
        self.assertEqual(game_state_response.current_round_name, "PRE_FLOP")
        self.assertTrue(game_state_response.status) # Game should be active

    def test_get_game_state_service(self):
        """Test retrieving game state via the service."""
        created_response = self.game_service.create_new_game_instance(self.start_game_request)
        self.assertIsNotNone(created_response)
        game_id = created_response.game_id

        retrieved_response = self.game_service.get_game_state(game_id, human_player_index=None)
        self.assertIsNotNone(retrieved_response)
        self.assertIsInstance(retrieved_response, GameStateResponse)
        self.assertEqual(retrieved_response.game_id, game_id)
        self.assertEqual(retrieved_response.player_count, 2)
        
        expected_stacks_after_blinds = [
            self.player_stacks[0] - self.blinds[1],  # P0 pays BB
            self.player_stacks[1] - self.blinds[0]   # P1 pays SB
        ]
        self.assertEqual(retrieved_response.stacks, expected_stacks_after_blinds)
        self.assertEqual(retrieved_response.button_index, 0)
        # After blinds and hole dealing, SB (Player 1) is the first to act.
        self.assertEqual(retrieved_response.actor_index, 1) 
        self.assertEqual(retrieved_response.current_round_name, "PRE_FLOP")

    def test_get_game_state_non_existent_service(self):
        """Test retrieving non-existent game state via the service."""
        non_existent_game_id = str(uuid.uuid4())
        retrieved_response = self.game_service.get_game_state(non_existent_game_id)
        self.assertIsNone(retrieved_response)

    def test_process_human_action_valid_call(self):
        """Test processing a valid human action (call)."""
        # Create a game where it's player 1's turn to act after blinds
        # Player 0 is BB (100), Player 1 is SB (50). Player 1 to act.
        game_state_response = self.game_service.create_new_game_instance(self.start_game_request)
        game_id = game_state_response.game_id
        pk_state_before_action = self.manager.get_game_state(game_id)
        
        self.assertIsNotNone(pk_state_before_action)
        self.assertEqual(pk_state_before_action.actor_index, 1) # Player 1 (SB) to act
        self.assertTrue(pk_state_before_action.can_check_or_call()) 
        # Call amount for SB (P1) is BB (100) - SB's current bet (50) = 50
        self.assertEqual(pk_state_before_action.checking_or_calling_amount, 50) 

        action_request = PlayerActionRequest(player_id="1", action_type="check_or_call")
        updated_response = self.game_service.process_human_action(game_id, action_request, human_player_index=1)
        
        self.assertIsInstance(updated_response, GameStateResponse)
        self.assertIsNone(updated_response.error_message)
        self.assertEqual(updated_response.bets, [100, 100]) # Both players have 100 in pot
        self.assertEqual(updated_response.pot_total, 200)
        # Actor should now be player 0 (or betting round ends if P1 was last to act before BB option)
        # With 2 players, after SB calls BB, BB has option if not all-in
        pk_state_after_action = self.manager.get_game_state(game_id)
        self.assertIsNotNone(pk_state_after_action)
        self.assertEqual(pk_state_after_action.actor_index, 0) # Player 0 (BB/Button) has option

    def test_process_human_action_invalid_action_wrong_player(self):
        """Test processing an action when it's not the specified player's turn."""
        game_state_response = self.game_service.create_new_game_instance(self.start_game_request)
        game_id = game_state_response.game_id
        # It's player 1's (SB) turn initially after hole dealing
        self.assertEqual(game_state_response.actor_index, 1)

        action_request = PlayerActionRequest(player_id="0", action_type="fold") # Player 0 (BB) tries to act
        # The service method itself now returns an error message for wrong player.
        updated_response = self.game_service.process_human_action(game_id, action_request, human_player_index=0)
        
        self.assertIsInstance(updated_response, GameStateResponse)
        # Expect an error message from the service
        self.assertIsNotNone(updated_response.error_message)
        if updated_response.error_message is not None: # Type guard for assertIn
            self.assertIn("Not player 0's turn", updated_response.error_message)
        self.assertEqual(updated_response.actor_index, 1) # Still player 1's turn
        self.assertEqual(updated_response.bets, [100, 50]) # Bets unchanged

    def test_process_human_action_invalid_raise_amount(self):
        """Test processing a raise action with an invalid (too small) amount."""
        game_state_response = self.game_service.create_new_game_instance(self.start_game_request)
        game_id = game_state_response.game_id
        # Player 1 (SB) to act, BB is 100.
        # Player 1 has 50 posted. To raise, min total bet is 2 * BB = 200.
        pk_state = self.manager.get_game_state(game_id)
        self.assertIsNotNone(pk_state)
        if pk_state: # Type guard
            self.assertEqual(pk_state.min_completion_betting_or_raising_to_amount, 200)

        action_request = PlayerActionRequest(player_id="1", action_type="raise", amount=120) # Raise to 120 (invalid)
        updated_response = self.game_service.process_human_action(game_id, action_request, human_player_index=1)
        
        self.assertIsInstance(updated_response, GameStateResponse)
        self.assertIsNotNone(updated_response.error_message)
        if updated_response.error_message is not None: # Type guard for assertIn
            self.assertIn("Invalid raise amount", updated_response.error_message)
        self.assertEqual(updated_response.actor_index, 1) # Still player 1's turn
        self.assertEqual(updated_response.bets, [100, 50]) # Bets unchanged

    # TODO: Add more tests for fold, check, different raise scenarios, all-ins, end of hand, etc.

if __name__ == '__main__':
    unittest.main()
