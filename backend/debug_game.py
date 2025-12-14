import asyncio
import sys
import os

# Add the backend directory to sys.path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.game_service import GameService
from app.core.poker_game_manager import PokerGameManager
from app.api.v1.poker_schemas import StartGameRequest

async def run_debug_game():
    print("--- Starting Debug Game Simulation ---")
    
    # 1. Initialize Service
    try:
        manager = PokerGameManager()
        service = GameService(manager)
        print("GameService initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize GameService: {e}")
        return

    # 2. Start a new game (Dummy vs Dummy)
    try:
        start_request = StartGameRequest(
            player_one_ai_type="dummy",
            player_two_ai_type="dummy",
            human_player_index=None, # Both AI
            initial_stacks=[1000, 1000],
            blinds=[5, 10]
        )
        game_state = service.create_new_game_instance(start_request)
        game_id = game_state.game_id
        print(f"\nGame Created! ID: {game_id}")
        print(f"Initial State: Status={game_state.status}, Round={game_state.current_round_name}")
        print(f"Pot: {game_state.pot_total}, Stacks: {game_state.stacks}")
        print(f"Actor Index: {game_state.actor_index}")
        print(f"Available Actions: {game_state.available_actions}")
        
    except Exception as e:
        print(f"Failed to create game: {e}")
        return

    # 3. Game Loop
    print("\n--- Entering Game Loop ---")
    max_turns = 20
    turn_count = 0
    
    while turn_count < max_turns:
        if not game_state.status:
            print("\n!!! Game Over !!!")
            break
            
        print(f"\n[Turn {turn_count + 1}] Current Round: {game_state.current_round_name}")
        print(f"Board: {game_state.board_cards}")
        
        try:
            # Advance AI Turn
            print(f"Requesting AI Turn (for Player {game_state.actor_index})...")
            # In a real scenario, we'd check whose turn it is. 
            # Since both are dummy AIs, we just call advance_ai_turn.
            
            game_state = await service.run_ai_vs_ai_game_turn(game_id)
            
            print(f"Turn Result: Actor={game_state.actor_index}, Pot={game_state.pot_total}")
            if game_state.last_action_details:
                print(f"Action Taken: {game_state.last_action_details}")
            else:
                print("No action details returned (or handling error).")
                
        except Exception as e:
            print(f"Error during turn execution: {e}")
            break
            
        turn_count += 1
        
    if turn_count >= max_turns:
        print("\n--- Max turns reached. Simulation stopped. ---")

    # 4. Final State
    print("\n--- Final Game State ---")
    print(f"Status: {game_state.status}")
    print(f"Round: {game_state.current_round_name}")
    print(f"Board: {game_state.board_cards}")
    print(f"Pot: {game_state.pot_total}")
    print(f"Stacks: {game_state.stacks}")
    if game_state.payoffs:
        print(f"Payoffs: {game_state.payoffs}")

if __name__ == "__main__":
    asyncio.run(run_debug_game())
