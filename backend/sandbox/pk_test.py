import sys
from decimal import Decimal

# Attempt to import pokerkit.
try:
    from pokerkit import NoLimitTexasHoldem, State, Automation, Mode, BlindOrStraddlePostingOperation
except ImportError as e:
    print(f"Failed to import pokerkit: {e}")
    print("Please ensure that the virtual environment is activated and pokerkit is installed.")
    sys.exit(1)

# Try to get version using getattr, or acknowledge if not found
pokerkit_version_str = "unknown"
try:
    import pokerkit
    pokerkit_version_str = getattr(pokerkit, '__version__', 'not found directly')
    if pokerkit_version_str == 'not found directly' and hasattr(pokerkit, 'VERSION'):  # common alternative
        pokerkit_version_str = pokerkit.VERSION
except ImportError:
    pass  # Already handled by the first try-except

print(f"Using pokerkit version: {pokerkit_version_str}, path: {NoLimitTexasHoldem.__module__}")

# ===== Integer-based Test (mirroring current poker_game_manager.py) =====
print("\n===== Integer-based Test =====")
player_stacks_int = [10000, 10000]
blinds_tuple_int = (50, 100)

ante_int = 0
current_min_bet_int = blinds_tuple_int[1]
player_count_int = len(player_stacks_int)

# Default automations as per PokerKit best practices/examples
default_automations_int = (
    Automation.ANTE_POSTING,
    Automation.BET_COLLECTION,
    Automation.BLIND_OR_STRADDLE_POSTING,
    Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
    Automation.HAND_KILLING,
    Automation.CHIPS_PUSHING,
    Automation.CHIPS_PULLING,
)

try:
    print("\nAttempting NoLimitTexasHoldem.create_state with integers...")
    state_int = NoLimitTexasHoldem.create_state(
        default_automations_int,  # automations
        False,                    # ante_trimming_status (uniform antes)
        ante_int,                 # raw_antes
        blinds_tuple_int,         # raw_blinds_or_straddles
        current_min_bet_int,      # min_bet
        player_stacks_int,        # raw_starting_stacks
        player_count_int,         # player_count
        mode=Mode.CASH_GAME       # mode
    )
    print("State created successfully with integers.")
    print(f"State type: {type(state_int)}")
    print(f"State dir (attributes): {dir(state_int)}")

    print("\n--- Attribute Inspection ---")
    attributes_to_check = ['button_index', 'actor_index', 'dealer_index', 'button', 'dealer', 'blinds_or_straddles']
    for attr in attributes_to_check:
        try:
            value = getattr(state_int, attr)
            print(f"state_int.{attr}: {value} (type: {type(value)})")
        except AttributeError:
            print(f"state_int.{attr}: Not found")
        except Exception as e:
            print(f"Error accessing state_int.{attr}: {type(e).__name__}: {e}")

    print("\n--- Specific Checks ---")
    # Check if blinds were posted by looking at stacks
    print(f"Initial stacks: {player_stacks_int}")
    print(f"Current stacks: {state_int.stacks}")
    if state_int.stacks[0] < player_stacks_int[0] or state_int.stacks[1] < player_stacks_int[1]:
        print("Blinds appear to have been posted.")
    else:
        print("Blinds do not appear to have been posted.")

    # Print operations to see if blind posting occurred
    print("\n--- Operations Log ---")
    button_player_index_from_ops = -1
    if hasattr(state_int, 'operations') and state_int.operations and hasattr(state_int, 'blinds_or_straddles'):
        small_blind_amount_configured = state_int.blinds_or_straddles[0]
        print(f"Configured small blind amount: {small_blind_amount_configured}")
        for op_idx, op in enumerate(state_int.operations):
            print(f"Op {op_idx}: {op} (type: {type(op)})")
            if isinstance(op, BlindOrStraddlePostingOperation) and op.amount == small_blind_amount_configured:
                button_player_index_from_ops = op.player_index
                print(f"  Found SB posting by player {op.player_index}, amount {op.amount}. Button set to {button_player_index_from_ops}.")
        if button_player_index_from_ops != -1:
            print(f"Determined button_player_index from operations: {button_player_index_from_ops}")
        else:
            print("Could not determine button player index from operations by matching SB amount.")
    else:
        print("No operations logged or operations/blinds_or_straddles attribute not found.")

except Exception as e:
    print(f"Error during state creation or inspection: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nSandbox script finished.")
