import pokerkit
import traceback



# Define default_automations (copied from conversation summary)
default_automations = [
    pokerkit.Automation.ANTE_POSTING,
    pokerkit.Automation.BET_COLLECTION,
    pokerkit.Automation.BLIND_OR_STRADDLE_POSTING,
    pokerkit.Automation.HOLE_DEALING,
    pokerkit.Automation.BOARD_DEALING,
    pokerkit.Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
    pokerkit.Automation.HAND_KILLING,
    pokerkit.Automation.CHIPS_PUSHING,
    pokerkit.Automation.CHIPS_PULLING,
]

try:
    # Based on logs: P1 is SB, P0 is BB.
    # In a 2-player game (Heads-Up):
    # The player who is SB is typically the Button. So, P1 is Button.
    # Blinds: P1 (Button) posts SB, P0 (Non-Button) posts BB.
    # Pre-flop action: P1 (Button/SB) acts first.
    # Post-flop action: P0 (Non-Button/BB) acts first.

    state = pokerkit.StandardTexasHoldem(
        automations=default_automations,
        blinds_or_straddles=(5, 10), # (SB amount, BB amount)
        stacks=[200, 200],          # Stacks for P0, P1
        player_dealer_button_index=1 # P1 is Button/SB
    )
    print(f"Initial state created. Player dealer button: {state.player_dealer_button_index} (P1 is Button)")
    # Expected blinds: P1 posts 5 (SB), P0 posts 10 (BB)

    state.start_hand()
    print(f"\nHand started. Initial Actor: {state.actor_index}, Street_index: {state.street_index}")
    
    # state.operate() handles automatic actions like blind posting and hole card dealing.
    state.operate() 
    print(f"\nAfter initial operate (blinds, hole cards):")
    current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index] if state.street_index is not None else "N/A"
    print(f"Actor: {state.actor_index}, Street: {current_street_name}, Board: {state.board_cards}")
    print(f"Stacks: P0={state.stacks[0]}, P1={state.stacks[1]}") # Expect P0=190, P1=195
    print(f"Bets: P0={state.bets[0]}, P1={state.bets[1]}")       # Expect P0=10, P1=5
    if state.hole_cards:
        print(f"Hole cards P0: {state.hole_cards[0]}, P1: {state.hole_cards[1]}")
    else:
        print("Hole cards not dealt or not accessible this way.")

    # Pre-flop betting sequence from logs:
    # P1 (Button/SB) calls.
    # P0 (BB) checks.

    # P1 (Button/SB) acts first pre-flop.
    if state.actor_index == 1:
        print(f"\nPlayer 1 (Button/SB) to act. Current bets: P0={state.bets[0]}, P1={state.bets[1]}")
        state.check_or_call() # P1 calls the BB (needs to add 5 to their current 5 to match 10)
        print(f"Player 1 (Button/SB) called.")
        state.operate() # Process P1's action
        current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
        print(f"After P1 calls and operate:")
        print(f"Actor: {state.actor_index}, Street: {current_street_name}, Board: {state.board_cards}")
        print(f"Stacks: P0={state.stacks[0]}, P1={state.stacks[1]}") # Expect P0=190, P1=190
        print(f"Bets: P0={state.bets[0]}, P1={state.bets[1]}")       # Expect P0=10, P1=10
    else:
        print(f"Expected P1 (Button/SB) to act pre-flop, but actor is {state.actor_index}.")

    # P0 (BB) acts next.
    if state.actor_index == 0:
        print(f"\nPlayer 0 (BB) to act. Current bets: P0={state.bets[0]}, P1={state.bets[1]}")
        state.check_or_call() # P0 checks (already posted BB of 10, P1 matched)
        print(f"Player 0 (BB) checked.")
        # This operate() should:
        # 1. Collect bets (BET_COLLECTION automation).
        # 2. Deal the flop (BOARD_DEALING automation).
        # 3. Advance the street.
        # 4. Set the new actor_index for the flop round (P0, as P0 is BB, first to act post-flop).
        state.operate() 
        current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
        print(f"After P0 checks and operate (should be start of Flop):")
        print(f"Actor: {state.actor_index}, Street: {current_street_name}, Board: {state.board_cards}")
        print(f"Stacks: P0={state.stacks[0]}, P1={state.stacks[1]}")
        print(f"Bets: P0={state.bets[0]}, P1={state.bets[1]}") # Bets should be 0
        print(f"Pot: {sum(pot.amount for pot in state.pots)}") # Pot should be 20
        print(f"Is hand over? {state.is_hand_over}")
    else:
        print(f"Expected P0 (BB) to act after P1, but actor is {state.actor_index}.")

    print(f"\nState after pre-flop betting completion attempt:")
    current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
    print(f"Actor: {state.actor_index}")
    print(f"Street: {current_street_name}")
    print(f"Board: {state.board_cards}")
    print(f"Pot: {sum(pot.amount for pot in state.pots)}")

    # --- Simulate Flop, Turn, River by checking down ---
    # Post-flop, action starts with P0 (BB, as P1 is Button).
    for street_name_target in ["FLOP", "TURN", "RIVER"]:
        current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
        
        if current_street_name != street_name_target:
            print(f"\nAttempting to simulate {street_name_target}, but current street is {current_street_name}. Stopping.")
            break
        
        if state.is_hand_over:
            print(f"\nHand ended before {street_name_target} betting round.")
            break
            
        if state.actor_index is None:
            print(f"\nActor is None before {street_name_target} betting round. Street not advancing as expected.")
            # Try one more operate to see if it helps deal the next street if board cards are missing for current street name
            if (street_name_target == "FLOP" and len(state.board_cards) < 3) or \
               (street_name_target == "TURN" and len(state.board_cards) < 4) or \
               (street_name_target == "RIVER" and len(state.board_cards) < 5):
                print(f"Board for {street_name_target} seems incomplete. Trying state.operate().")
                state.operate()
                current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
                print(f"After extra operate: Actor: {state.actor_index}, Street: {current_street_name}, Board: {state.board_cards}")
                if state.actor_index is None and current_street_name == street_name_target: # Still no actor after operate
                     print(f"Still no actor for {street_name_target} after extra operate. Stopping.")
                     break
            else: # Actor is None, but board seems complete for the street name, or it's not a board issue.
                print(f"Actor is None at start of {street_name_target} betting. Stopping.")
                break


        print(f"\n--- {current_street_name} Betting ---")
        print(f"Actor: {state.actor_index}, Board: {state.board_cards}, Stacks: P0={state.stacks[0]}, P1={state.stacks[1]}, Bets: P0={state.bets[0]}, P1={state.bets[1]}")

        # Players check down the street
        # P0 (BB) acts first post-flop.
        if state.actor_index == 0 and 0 in state.player_indices_in_hand:
            print(f"Player 0 (BB) acts on {current_street_name}.")
            state.check_or_call()
            print(f"Player 0 (BB) checks.")
            state.operate()
            print(f"After P0 checks and operate: Actor: {state.actor_index}, Bets: P0={state.bets[0]}, P1={state.bets[1]}")

        # P1 (Button/SB) acts next.
        if state.actor_index == 1 and 1 in state.player_indices_in_hand: # Check if P1 is still in hand
            print(f"Player 1 (Button/SB) acts on {current_street_name}.")
            state.check_or_call()
            print(f"Player 1 (Button/SB) checks.")
            # This operate() should collect bets, deal the next street's board cards (if any),
            # advance street_index, and set the new actor.
            state.operate() 
            current_street_name_after_betting = pokerkit.StandardTexasHoldem.street_names[state.street_index]
            print(f"After P1 checks and operate (end of {current_street_name} betting):")
            print(f"Actor: {state.actor_index}, Street: {current_street_name_after_betting}, Board: {state.board_cards}")
            print(f"Bets: P0={state.bets[0]}, P1={state.bets[1]}, Pot: {sum(pot.amount for pot in state.pots)}")
        
        if state.is_hand_over: # Check if hand ended after this street's betting
            print(f"Hand ended after {current_street_name} betting.")
            break
        
        # If after P1's action, the actor is still P1 or P0, it means the betting round isn't over (e.g. a bet was made and needs a response)
        # For a simple check-check scenario, actor should become None (if street ends) or switch to the first player of the next street.
        # The main loop condition (current_street_name != street_name_target) will handle advancing to next iteration.

    if state.is_hand_over:
        print("\n--- Hand Over ---")
        current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
        print(f"Final Street: {current_street_name}, Final Board: {state.board_cards}")
        print(f"Final Stacks: P0={state.stacks[0]}, P1={state.stacks[1]}")
        print(f"Pots: {[p.amount for p in state.pots]}")
        # Determine winner by looking at who has more chips if CHIPS_PUSHING/PULLING worked,
        # or by inspecting state.payoffs if available and populated.
        # For this test, seeing showdown (RIVER street completed) is key.
        if current_street_name == "RIVER" and not any(state.bets): # Betting done on river
             print("Showdown occurred or hand ended after river betting.")
    else:
        print("\n--- Simulation Incomplete or Hand Ongoing ---")
        current_street_name = pokerkit.StandardTexasHoldem.street_names[state.street_index]
        print(f"Ended at Street: {current_street_name}, Actor: {state.actor_index}, Board: {state.board_cards}")
        print(f"Stacks: P0={state.stacks[0]}, P1={state.stacks[1]}, Bets: P0={state.bets[0]}, P1={state.bets[1]}")

except ImportError:
    print("PokerKit not imported correctly at the start of the script.")
except pokerkit.PokerKitError as e:
    print(f"A PokerKitError occurred during game simulation: {e}")
    traceback.print_exc()
except AttributeError as e:
    print(f"AttributeError during simulation: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"An unexpected error occurred during game simulation: {e}")
    traceback.print_exc()
