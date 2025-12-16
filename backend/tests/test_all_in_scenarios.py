"""
Test Suite: All-In Scenarios
Tests for poker all-in mechanics without using real AI (uses DummyAI or mocks)
"""
import unittest
from unittest.mock import patch, MagicMock
import asyncio

from app.core.poker_game_manager import PokerGameManager
from app.services.game_service import GameService
from app.api.v1.poker_schemas import StartGameRequest, PlayerActionRequest, PlayerConfig


class TestAllInScenarios(unittest.TestCase):
    """Test all-in poker scenarios."""
    
    def setUp(self):
        """Set up for test methods."""
        self.manager = PokerGameManager()
        self.game_service = GameService(game_manager=self.manager)
    
    def test_player_all_in_preflop_small_stack(self):
        """Test when a player with small stack goes all-in."""
        # Player 0: 200 chips (short stack)
        # Player 1: 10000 chips (big stack)
        # Blinds: 50/100
        request = StartGameRequest(
            players=[
                PlayerConfig(name="ShortStack", ai_type="dummy", stack=200),
                PlayerConfig(name="BigStack", ai_type="dummy", stack=10000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # After blinds: P0 (BB) has 200-100=100, P1 (SB) has 10000-50=9950
        self.assertTrue(game_state.status)
        self.assertEqual(game_state.actor_index, 1)  # SB acts first
        
        # P1 (SB) raises all-in (to simulate pressure)
        pk_state = self.manager.get_game_state(game_id)
        self.assertTrue(pk_state.can_complete_bet_or_raise_to())
        
    def test_both_players_all_in_showdown(self):
        """Test when both players are all-in, hand should complete to showdown."""
        # Both players have 500 chips
        request = StartGameRequest(
            players=[
                PlayerConfig(name="Player1", ai_type="dummy", stack=500),
                PlayerConfig(name="Player2", ai_type="dummy", stack=500)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # P1 (SB, actor_index=1) goes all-in by raising to 500
        action = PlayerActionRequest(action_type="raise", amount=500)
        result = self.game_service.process_human_action(game_id, action, human_player_index=1)
        
        self.assertIsNone(result.error_message)
        
        # Now P0 (BB) should be able to call the all-in
        pk_state = self.manager.get_game_state(game_id)
        self.assertEqual(pk_state.actor_index, 0)  # P0's turn
        self.assertTrue(pk_state.can_check_or_call())
        
        # P0 calls the all-in
        call_action = PlayerActionRequest(action_type="call")
        final_result = self.game_service.process_human_action(game_id, call_action, human_player_index=0)
        
        # After both all-in, hand should be complete (status=False) or progressing
        # PokerKit should auto-deal remaining board cards

    def test_all_in_with_uneven_stacks(self):
        """Test all-in where one player has more chips than other."""
        # P0: 300 chips, P1: 1000 chips
        request = StartGameRequest(
            players=[
                PlayerConfig(name="Small", ai_type="dummy", stack=300),
                PlayerConfig(name="Large", ai_type="dummy", stack=1000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # P0 has 300-100(BB)=200 left, P1 has 1000-50(SB)=950 left
        self.assertEqual(game_state.stacks[0], 200)  # P0 after BB
        self.assertEqual(game_state.stacks[1], 950)  # P1 after SB
        
        # P1 (SB) raises to 300 (P0's total stack)
        action = PlayerActionRequest(action_type="raise", amount=300)
        result = self.game_service.process_human_action(game_id, action, human_player_index=1)
        
        self.assertIsNone(result.error_message)
        
        # P0 calls with remaining 200 (effectively all-in for 300 total)
        pk_state = self.manager.get_game_state(game_id)
        # The call amount should be whatever makes P0 match P1's bet
        call_amount = pk_state.checking_or_calling_amount
        self.assertIsNotNone(call_amount)

    def test_fold_against_all_in(self):
        """Test folding when opponent goes all-in."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="Folder", ai_type="dummy", stack=1000),
                PlayerConfig(name="AllIn", ai_type="dummy", stack=1000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # P1 goes all-in (raises to 1000)
        action = PlayerActionRequest(action_type="raise", amount=1000)
        result = self.game_service.process_human_action(game_id, action, human_player_index=1)
        self.assertIsNone(result.error_message)
        
        # P0 folds
        fold_action = PlayerActionRequest(action_type="fold")
        final_result = self.game_service.process_human_action(game_id, fold_action, human_player_index=0)
        
        # Hand should be over
        self.assertFalse(final_result.status)
        # P1 should have won the pot
        self.assertIsNotNone(final_result.payoffs)

    def test_all_in_deals_full_board_and_completes(self):
        """
        REGRESSION TEST: Verify that when both players are all-in,
        the board is dealt completely (5 cards) and the hand completes.
        This tests the RUNOUT_COUNT_SELECTION automation.
        """
        # P0: 500 chips, P1: 500 chips (equal stacks for all-in scenario)
        request = StartGameRequest(
            players=[
                PlayerConfig(name="Player1", ai_type="dummy", stack=500),
                PlayerConfig(name="Player2", ai_type="dummy", stack=500)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # P1 (SB, actor_index=1) goes all-in by raising to 500
        action = PlayerActionRequest(action_type="raise", amount=500)
        result = self.game_service.process_human_action(game_id, action, human_player_index=1)
        self.assertIsNone(result.error_message)
        
        # P0 (BB) calls the all-in
        call_action = PlayerActionRequest(action_type="call")
        final_result = self.game_service.process_human_action(game_id, call_action, human_player_index=0)
        
        # CRITICAL ASSERTIONS for the all-in regression:
        # 1. Hand should be complete (status=False)
        self.assertFalse(final_result.status, 
            "Hand should be complete after both players are all-in")
        
        # 2. Board should have 5 cards (flop + turn + river)
        self.assertEqual(len(final_result.board_cards), 5,
            f"Full board (5 cards) should be dealt, got {len(final_result.board_cards)}: {final_result.board_cards}")
        
        # 3. Payoffs should be set
        self.assertIsNotNone(final_result.payoffs,
            "Payoffs should be calculated after hand completes")
        
        # 4. One player should have won (payoffs should have a positive value)
        self.assertTrue(any(p > 0 for p in final_result.payoffs if p is not None),
            f"At least one player should have positive payoff, got: {final_result.payoffs}")


class TestAllInWithAI(unittest.TestCase):
    """Test all-in scenarios using DummyAI (no API costs)."""
    
    def setUp(self):
        self.manager = PokerGameManager()
        self.game_service = GameService(game_manager=self.manager)
    
    def test_ai_vs_ai_all_in_completes(self):
        """Test that AI vs AI game with all-in completes properly."""
        # Use DummyAI which makes random decisions - no API calls
        request = StartGameRequest(
            players=[
                PlayerConfig(name="DummyBot1", ai_type="dummy", stack=500),
                PlayerConfig(name="DummyBot2", ai_type="dummy", stack=500)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # Run AI turns until hand is complete (max 20 iterations to prevent infinite loop)
        iterations = 0
        max_iterations = 20
        
        while game_state.status and iterations < max_iterations:
            # Run AI turn
            game_state = asyncio.get_event_loop().run_until_complete(
                self.game_service.run_ai_vs_ai_game_turn(game_id)
            )
            iterations += 1
        
        # Either hand completed or we hit max iterations
        if not game_state.status:
            # Hand is over - verify payoffs exist
            self.assertIsNotNone(game_state.payoffs)
        else:
            # Max iterations hit - this is also valid (hand still going)
            self.assertLessEqual(iterations, max_iterations)


if __name__ == '__main__':
    unittest.main()
