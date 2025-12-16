"""
Test Suite: Game State Transitions
Tests for hand progression, street transitions, and game flow
"""
import unittest

from app.core.poker_game_manager import PokerGameManager
from app.services.game_service import GameService
from app.api.v1.poker_schemas import StartGameRequest, PlayerActionRequest, PlayerConfig


class TestStreetProgression(unittest.TestCase):
    """Test street-by-street progression through a hand."""
    
    def setUp(self):
        self.manager = PokerGameManager()
        self.game_service = GameService(game_manager=self.manager)
        
        # Standard game with 10k stacks
        self.request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=10000),
                PlayerConfig(name="P2", ai_type="dummy", stack=10000)
            ],
            blinds=[50, 100]
        )
    
    def test_initial_state_is_preflop(self):
        """Test that new game starts at preflop."""
        game_state = self.game_service.create_new_game_instance(self.request)
        
        self.assertEqual(game_state.current_round_name, "PRE_FLOP")
        self.assertEqual(len(game_state.board_cards), 0)
        self.assertTrue(game_state.status)
    
    def test_preflop_to_flop_transition(self):
        """Test transition from preflop to flop after betting completes."""
        game_state = self.game_service.create_new_game_instance(self.request)
        game_id = game_state.game_id
        
        # P1 (SB) calls
        call_action = PlayerActionRequest(action_type="call")
        result = self.game_service.process_human_action(game_id, call_action, human_player_index=1)
        
        # P0 (BB) checks (has option)
        check_action = PlayerActionRequest(action_type="check")
        result = self.game_service.process_human_action(game_id, check_action, human_player_index=0)
        
        # Should now be on flop
        pk_state = self.manager.get_game_state(game_id)
        if pk_state.status:  # If hand continues
            self.assertGreaterEqual(len(pk_state.board_cards), 3)
    
    def test_fold_ends_hand_immediately(self):
        """Test that a fold ends the hand immediately."""
        game_state = self.game_service.create_new_game_instance(self.request)
        game_id = game_state.game_id
        
        # P1 (SB) folds immediately
        fold_action = PlayerActionRequest(action_type="fold")
        result = self.game_service.process_human_action(game_id, fold_action, human_player_index=1)
        
        # Hand should be over
        self.assertFalse(result.status)
        self.assertEqual(result.current_round_name, "HAND_OVER")
    
    def test_check_check_continues_hand(self):
        """Test that check-check moves to next street."""
        game_state = self.game_service.create_new_game_instance(self.request)
        game_id = game_state.game_id
        
        # P1 (SB) calls (to match BB)
        call_action = PlayerActionRequest(action_type="call")
        self.game_service.process_human_action(game_id, call_action, human_player_index=1)
        
        # P0 (BB) checks
        check_action = PlayerActionRequest(action_type="check")
        result = self.game_service.process_human_action(game_id, check_action, human_player_index=0)
        
        # Hand should continue (flop or beyond)
        pk_state = self.manager.get_game_state(game_id)
        self.assertTrue(pk_state.status)


class TestBettingRounds(unittest.TestCase):
    """Test betting round mechanics."""
    
    def setUp(self):
        self.manager = PokerGameManager()
        self.game_service = GameService(game_manager=self.manager)
    
    def test_raise_changes_actor_back(self):
        """Test that a raise gives action back to opponent."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=10000),
                PlayerConfig(name="P2", ai_type="dummy", stack=10000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # Initial actor is P1 (SB)
        self.assertEqual(game_state.actor_index, 1)
        
        # P1 raises to 300
        raise_action = PlayerActionRequest(action_type="raise", amount=300)
        result = self.game_service.process_human_action(game_id, raise_action, human_player_index=1)
        
        # Now P0 should be actor
        self.assertEqual(result.actor_index, 0)
        
        # P0 re-raises to 600
        reraise_action = PlayerActionRequest(action_type="raise", amount=600)
        result = self.game_service.process_human_action(game_id, reraise_action, human_player_index=0)
        
        # Now P1 should be actor again
        self.assertEqual(result.actor_index, 1)
    
    def test_call_after_raise_ends_betting_round(self):
        """Test that calling a raise ends the betting round."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=10000),
                PlayerConfig(name="P2", ai_type="dummy", stack=10000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # P1 (SB) calls
        call_action = PlayerActionRequest(action_type="call")
        result = self.game_service.process_human_action(game_id, call_action, human_player_index=1)
        
        # P0 (BB) raises to 300
        raise_action = PlayerActionRequest(action_type="raise", amount=300)
        result = self.game_service.process_human_action(game_id, raise_action, human_player_index=0)
        
        # P1 calls the raise
        call_action = PlayerActionRequest(action_type="call")
        result = self.game_service.process_human_action(game_id, call_action, human_player_index=1)
        
        # Betting round should be complete - should be on flop now
        pk_state = self.manager.get_game_state(game_id)
        self.assertGreaterEqual(len(pk_state.board_cards), 3)  # Flop dealt


class TestHoleCards(unittest.TestCase):
    """Test hole card dealing and visibility."""
    
    def setUp(self):
        self.manager = PokerGameManager()
        self.game_service = GameService(game_manager=self.manager)
    
    def test_both_players_have_hole_cards(self):
        """Test that both players receive exactly 2 hole cards."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=10000),
                PlayerConfig(name="P2", ai_type="dummy", stack=10000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        
        # Both players should have 2 cards
        self.assertIn(0, game_state.player_hole_cards)
        self.assertIn(1, game_state.player_hole_cards)
        self.assertEqual(len(game_state.player_hole_cards[0]), 2)
        self.assertEqual(len(game_state.player_hole_cards[1]), 2)
    
    def test_hole_cards_are_valid_format(self):
        """Test that hole cards are in valid format (e.g., 'Ah', 'Kd')."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=10000),
                PlayerConfig(name="P2", ai_type="dummy", stack=10000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        
        valid_ranks = set('23456789TJQKA')
        valid_suits = set('cdhs')
        
        for player_idx in [0, 1]:
            for card in game_state.player_hole_cards[player_idx]:
                self.assertEqual(len(card), 2)
                self.assertIn(card[0], valid_ranks)
                self.assertIn(card[1], valid_suits)


class TestPotCalculation(unittest.TestCase):
    """Test pot calculation accuracy."""
    
    def setUp(self):
        self.manager = PokerGameManager()
        self.game_service = GameService(game_manager=self.manager)
    
    def test_pot_after_blinds(self):
        """Test pot size immediately after blinds posted."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=1000),
                PlayerConfig(name="P2", ai_type="dummy", stack=1000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        
        # Pot should be SB + BB = 150
        self.assertEqual(game_state.pot_total, 150)
    
    def test_pot_after_call(self):
        """Test pot size after SB calls BB."""
        request = StartGameRequest(
            players=[
                PlayerConfig(name="P1", ai_type="dummy", stack=1000),
                PlayerConfig(name="P2", ai_type="dummy", stack=1000)
            ],
            blinds=[50, 100]
        )
        
        game_state = self.game_service.create_new_game_instance(request)
        game_id = game_state.game_id
        
        # P1 (SB) calls
        call_action = PlayerActionRequest(action_type="call")
        result = self.game_service.process_human_action(game_id, call_action, human_player_index=1)
        
        # Pot should be 100 + 100 = 200
        self.assertEqual(result.pot_total, 200)


if __name__ == '__main__':
    unittest.main()
