import asyncio
import os
import sys
import uuid
import time
import json
import logging
from typing import List, Dict

# Add backend to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.poker_game_manager import PokerGameManager
from app.services.game_service import GameService
from app.api.v1.poker_schemas import StartGameRequest, PlayerConfig
from backend.experiments.db_client import DBClient
from backend.experiments.cost_tracker import CostTracker

# Import AI classes directly to bypass service factory if needed, 
# but GameService is convenient for state translation.
from app.ai.gemini_ai import GeminiAI
# from app.ai.claude_ai import ClaudeAI (Import when available)
# from app.ai.x_ai import XAI (Import when available)

class ExperimentRunner:
    def __init__(self, agents: List[Dict], hands_to_play: int = 10, budget_limit: float = 15.0):
        self.agents_config = agents
        self.hands_to_play = hands_to_play
        self.num_players = len(agents)
        self.db = DBClient()
        self.cost_tracker = CostTracker(budget_limit=budget_limit)
        
        self.experiment_id = f"exp_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        self.manager = PokerGameManager()
        self.service = GameService(self.manager)
        
        # Initialize Bankrolls (start fresh or load?)
        # For now, start everyone with 100BB (10,000 chips)
        self.current_stacks = [10000] * self.num_players
        
        # Log start
        self.db.create_experiment(self.experiment_id, {"agents": agents, "budget": budget_limit})
        print(f"🧪 Experiment {self.experiment_id} initialized.")
        print(f"👥 Agents: {[a['model'] for a in agents]}")

    async def run_tournament(self):
        """Main Loop"""
        button_index = 0
        
        for hand_num in range(1, self.hands_to_play + 1):
            if self.cost_tracker.is_over_budget():
                print("💰 Budget cap reached! Stopping tournament.")
                break
                
            print(f"\n--- 🃏 Dealing Hand {hand_num}/{self.hands_to_play} ---")
            
            # 1. Setup Request
            # We must recreate the game for each hand to reset deck/state in this architecture
            # But we pass in the 'current_stacks' to simulate a continuous session.
            
            player_configs = []
            for i, agent in enumerate(self.agents_config):
                # Ensure they have at least 1 chip
                stack = max(1, self.current_stacks[i])
                player_configs.append(PlayerConfig(
                    name=agent['name'],
                    ai_type=agent['ai_type'],
                    stack=stack,
                    gemini_model=agent.get('model') if agent['ai_type'] == 'gemini' else None
                    # Add other model fields here
                ))

            req = StartGameRequest(
                players=player_configs,
                blinds=[50, 100],
                initial_stacks=[p.stack for p in player_configs] # Redundant but safe
            )
            
            # Create Game Instance
            # NOTE: GameService usually creates a NEW game_id. 
            # We will use this game_id for this single hand.
            game_state = self.service.create_new_game_instance(req)
            game_id = game_state.game_id
            
            # Force Button Position (if Manager supports it, otherwise it's random/0)
            # Improving GameService to accept button_index would be good, but for now let's accept default
            # Actually, `create_game` in manager accepts button_index, but service `create_new_game_instance` doesn't expose it.
            # We can manually hack it or just accept rotation might be static.
            # Research Rigor: We SHOULD rotate. 
            # Hack: access manager directly
            pk_state = self.manager.get_game_state(game_id)
            if pk_state:
                pk_state.button_index = button_index % self.num_players
            
            # 2. Play the Hand
            winner_model = None
            pot_size = 0
            hand_id = f"{self.experiment_id}_h{hand_num}"
            
            # Log hand start
            self.db.log_hand(hand_id, self.experiment_id, hand_num, [], 0, "TBD", "TBD")
            
            while game_state.status: # While game is active
                # Check whose turn it is
                actor_idx = game_state.actor_index
                if actor_idx is None:
                    # Should not happen in loop unless all-in runout
                    # Run logic to finish hand
                    game_state = await self.service.run_ai_vs_ai_game_turn(game_id)
                    continue

                agent_cfg = self.agents_config[actor_idx]
                
                # Check Budget BEFORE Acting
                if self.cost_tracker.is_over_budget():
                    print("Budget kill switch active.")
                    break
                
                # Run Turn
                # We need to intercept the `run_ai_vs_ai_game_turn` call to log cost
                # OR we trust the service.
                # Problem: Service doesn't return Token Usage.
                # Solution: Wrapper or Estimate.
                # For this version, let's Estimate based on prompt size + response.
                
                # We will call the specific AI logic manually here?
                # No, that duplicates `GameService` logic.
                # Better: Modify `GameService` or `BaseAI` to return usage.
                # Or: Just run the Service and accept we only have 'Estimate' tracking.
                
                start_time = time.time()
                game_state = await self.service.run_ai_vs_ai_game_turn(game_id)
                duration = time.time() - start_time
                
                # Retrieve the last action details to log
                if game_state.last_action_details:
                    details = game_state.last_action_details
                    if details.get('player_index') == actor_idx:
                        # Log it
                        # Estimate Cost (Rough: 1000 input chars, 50 output chars)
                        # TODO: Make this accurate by parsing the prompt inside AI classes
                        cost = self.cost_tracker.track_usage(
                            agent_cfg.get('model', 'default'), 
                            input_tokens=1000, # Mock 
                            output_tokens=50   # Mock
                        )
                        
                        self.db.log_action(
                            hand_id,
                            game_state.current_round_name,
                            agent_cfg['model'],
                            details.get('action', 'unknown'),
                            details.get('amount', 0),
                            game_state.ai_message or "",
                            {"cost": cost}
                        )
                        print(f"  > {agent_cfg['name']}: {details.get('action')} (${cost:.4f})")
            
            # 3. Hand Over - Update Stacks
            # game_state.stacks now has final chips
            print(f"  🏁 Hand {hand_num} Complete. Winner: {game_state.winning_hand_name}")
            
            self.current_stacks = game_state.stacks
            
            # Log Result
            winner_idx = game_state.winning_player_index
            winner_name = "Split/Tie"
            if winner_idx is not None:
                winner_name = self.agents_config[winner_idx]['model']
            
            self.db.log_hand(
                hand_id, self.experiment_id, hand_num, 
                game_state.board_cards, game_state.pot_total, 
                winner_name, game_state.winning_hand_name
            )
            
            # Update Persistent Stacks
            # Also log stack history
            for i, stack in enumerate(self.current_stacks):
                self.db.log_stack_update(hand_id, self.agents_config[i]['model'], 0, stack) # Todo: track start/end properly

            button_index += 1
            
            # Clean up memory
            self.manager.remove_game(game_id)

if __name__ == "__main__":
    # Test Configuration
    AGENTS = [
        {"name": "Gemini Pro", "ai_type": "gemini", "model": "gemini-1.5-pro-002"},
        {"name": "Gemini Flash", "ai_type": "gemini", "model": "gemini-1.5-flash-002"}
    ]
    
    runner = ExperimentRunner(AGENTS, hands_to_play=5, budget_limit=0.50)
    asyncio.run(runner.run_tournament())
