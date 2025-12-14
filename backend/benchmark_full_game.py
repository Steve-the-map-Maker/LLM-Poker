
import asyncio
import time
import sys
import os

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.poker_game_manager import PokerGameManager
from app.services.game_service import GameService
from app.api.v1.poker_schemas import StartGameRequest

async def benchmark_game():
    print("--- Starting Poker Benchmark ---")
    
    # 1. Setup
    manager = PokerGameManager()
    service = GameService(manager)
    
    # Create a 2-player game (Dummy vs Dummy for baseline speed)
    # Note: Currently limited to 2 players by schema, but manager supports more.
    # We will bypass schema validation for the manager creation if possible, 
    # but GameService expects the request. For now, strict 2 player benchmark.
    
    req = StartGameRequest(
        player_one_ai_type="dummy",
        player_two_ai_type="dummy",
        human_player_index=None, # AI vs AI
        initial_stacks=[10000, 10000],
        blinds=[50, 100]
    )
    
    start_time = time.time()
    game_response = service.create_new_game_instance(req)
    game_id = game_response.game_id
    setup_time = time.time() - start_time
    print(f"Game Setup Time: {setup_time:.4f}s")
    
    # 2. Run Game Loop (One complete hand)
    turn_count = 0
    game_active = True
    
    total_logic_time = 0
    total_ai_time = 0 # Included in logic time roughly, but we can't separate easily without instrumentation inside service
    
    print(f"Game ID: {game_id}. Starting Loop...")
    
    while game_active:
        loop_start = time.time()
        
        # Determine valid check - service.run_ai_vs_ai_game_turn checks internal state
        try:
            # We call the service's turn function
            # This includes:
            # A) Getting state (fast)
            # B) AI processing (Get action) -> Dummy is fast, LLM is slow
            # C) PokerKit Update (fast)
            
            # Since we are using DummyAI, this effectively measures "Logic Overhead"
            new_state = await service.run_ai_vs_ai_game_turn(game_id)
            
            if not new_state.status:
                game_active = False
                print("Hand Ended.")
            else:
                turn_count += 1
                
        except Exception as e:
            print(f"Error in loop: {e}")
            break
            
        loop_duration = time.time() - loop_start
        total_logic_time += loop_duration
        
        # Safety break
        if turn_count > 100:
            print("Force stopping after 100 turns.")
            break
            
    total_time = time.time() - start_time
    avg_turn_time = total_logic_time / turn_count if turn_count > 0 else 0
    
    print(f"\n--- Benchmark Results ---")
    print(f"Total Time: {total_time:.4f}s")
    print(f"Total Turns: {turn_count}")
    print(f"Avg Time per Turn: {avg_turn_time:.4f}s")
    print("-------------------------")

if __name__ == "__main__":
    asyncio.run(benchmark_game())
