import pokerkit
from typing import List

def format_poker_state_for_llm(pk_state: pokerkit.State, player_index_for_ai: int, game_id: str, player_name: str, history: List[str]) -> str:
    """
    Formats the current poker game state into a detailed text prompt for an LLM.
    Uses PokerKit State object to extract comprehensive game information.
    """
    try:
        # --- Basic Game Information ---
        prompt_parts = [f"You are an expert Texas Hold'em poker player named '{player_name}'. This is game ID: {game_id}."]
        
        # Get player count safely
        player_count = getattr(pk_state, 'player_count', 2)  # Default to 2 if not found
        prompt_parts.append(f"You are Player {player_index_for_ai + 1} out of {player_count} players.")
        
        # --- Your Hand ---
        try:
            your_hole_cards_obj = pk_state.hole_cards[player_index_for_ai]  # Direct access for the AI itself
            your_cards_str = " and ".join([f"{card.rank.value}{card.suit.value}" for card in your_hole_cards_obj]) if your_hole_cards_obj else "No cards dealt yet / Folded"
        except (AttributeError, IndexError):
            your_cards_str = "Unable to determine cards"
            
        prompt_parts.append(f"Your hole cards: {your_cards_str}.")
        
        # --- Community Cards ---
        try:
            board_cards_obj = pk_state.board_cards
            board_str = " ".join([f"{card.rank.value}{card.suit.value}" for card in board_cards_obj]) if board_cards_obj else "None"
        except AttributeError:
            board_str = "None"
            
        street_map = {0: "Preflop (no community cards yet)", 1: "Flop", 2: "Turn", 3: "River"}
        try:
            betting_round_name = street_map.get(pk_state.street_index, "Unknown Round")
        except AttributeError:
            betting_round_name = "Unknown Round"
            
        prompt_parts.append(f"Betting Round: {betting_round_name}.")
        prompt_parts.append(f"Community cards (Board): {board_str}.")
        
        # --- Pot and Stacks ---
        try:
            pot_amount = getattr(pk_state, 'total_pot_amount', 0)
            prompt_parts.append(f"Total pot size: {pot_amount} chips.")
        except (AttributeError, TypeError):
            prompt_parts.append("Total pot size: Unknown.")
            
        try:
            your_stack = pk_state.stacks[player_index_for_ai]
            prompt_parts.append(f"Your current stack: {your_stack} chips.")
            
            for i in range(player_count):
                if i != player_index_for_ai:
                    opponent_name = f"Player {i + 1}"  # In a 2-player game, this is simple. For more, use game_player_identities
                    prompt_parts.append(f"Opponent ({opponent_name}) stack: {pk_state.stacks[i]} chips.")
        except (AttributeError, IndexError):
            prompt_parts.append("Stack information unavailable.")
        
        # --- Blinds and Button ---
        try:
            button_index = getattr(pk_state, 'button_index', 0)  # Default to 0 if not found
            prompt_parts.append(f"Player {button_index + 1} is the dealer button.")
        except AttributeError:
            prompt_parts.append("Dealer button position unknown.")
            
        # Small blind amount: pk_state.blinds_or_straddles[0] (assuming standard blind structure)
        # Big blind amount: pk_state.blinds_or_straddles[1]
        try:
            sb = pk_state.blinds_or_straddles[0] if hasattr(pk_state, 'blinds_or_straddles') and len(pk_state.blinds_or_straddles) > 0 else 5
            bb = pk_state.blinds_or_straddles[1] if hasattr(pk_state, 'blinds_or_straddles') and len(pk_state.blinds_or_straddles) > 1 else 10
            prompt_parts.append(f"Small blind: {sb}, Big blind: {bb}.")
        except Exception:
            prompt_parts.append("Blind information unavailable.")
        
        # --- Action History (Simplified from pk_state.operations) ---
        prompt_parts.append("\n--- Action History This Hand ---")
        try:
            operations = getattr(pk_state, 'operations', [])
            if not operations:
                prompt_parts.append("No actions yet in this hand.")
            else:
                for op in operations:
                    # Format pokerkit.Operation objects into readable strings.
                    try:
                        player_idx = getattr(op, 'player_index', 0)
                        op_player_name = f"Player {player_idx + 1}"  # Needs actual name from GameService context
                        op_detail = ""
                        if isinstance(op, pokerkit.AntePostingOperation): 
                            op_detail = f"posts ante {op.amount}"
                        elif isinstance(op, pokerkit.BlindOrStraddlePostingOperation): 
                            op_detail = f"posts {op.type_name.lower() if hasattr(op, 'type_name') else 'blind'} {op.amount}"
                        elif isinstance(op, pokerkit.FoldingOperation): 
                            op_detail = "folds"
                        elif isinstance(op, pokerkit.CheckingOrCallingOperation): 
                            op_detail = f"calls {op.amount}" if op.amount > 0 else "checks"
                        elif isinstance(op, pokerkit.CompletionBettingOrRaisingToOperation): 
                            op_detail = f"raises to {op.amount}"
                        # Add more for other operation types if needed
                        if op_detail: 
                            prompt_parts.append(f"{op_player_name} {op_detail}.")
                    except (AttributeError, IndexError) as e:
                        prompt_parts.append(f"Operation details unavailable: {e}")
        except (AttributeError, TypeError) as e:
            prompt_parts.append(f"Action history unavailable: {e}")
        
        # --- Current Situation & Valid Actions ---
        prompt_parts.append("\n--- Your Turn ---")
        try:
            amount_to_call = getattr(pk_state, 'checking_or_calling_amount', 0)
            prompt_parts.append(f"Current bet to you: {amount_to_call} chips.")
            prompt_parts.append("Valid actions for you:")
            actions_list = []
            
            can_fold = hasattr(pk_state, 'can_fold') and callable(pk_state.can_fold) and pk_state.can_fold()
            can_check_or_call = hasattr(pk_state, 'can_check_or_call') and callable(pk_state.can_check_or_call) and pk_state.can_check_or_call()
            can_raise = hasattr(pk_state, 'can_complete_bet_or_raise_to') and callable(pk_state.can_complete_bet_or_raise_to) and pk_state.can_complete_bet_or_raise_to()
            
            if can_fold: 
                actions_list.append("FOLD")
            if can_check_or_call:
                if amount_to_call == 0: 
                    actions_list.append("CHECK")
                else: 
                    actions_list.append(f"CALL")  # LLM should know to call 'amount_to_call'
            
            try:
                min_raise = getattr(pk_state, 'min_completion_betting_or_raising_to_amount', None)
                max_raise = getattr(pk_state, 'max_completion_betting_or_raising_to_amount', None)
                if can_raise and min_raise is not None and max_raise is not None and min_raise <= max_raise:
                    actions_list.append(f"RAISE_TO <total_amount> (min: {min_raise}, max: {max_raise})")
            except AttributeError:
                pass
                
            if actions_list:
                prompt_parts.append(", ".join(actions_list) + ".")
            else:
                prompt_parts.append("No valid actions found. Default to FOLD.")
        except Exception as e:
            prompt_parts.append(f"Error determining valid actions: {e}. Default to FOLD.")
        
        # --- Output Instruction ---
        prompt_parts.append("\n--- Your Decision ---")
        prompt_parts.append("Respond with your chosen action in ONE LINE, using ONE of the following formats:")
        prompt_parts.append("- FOLD")
        prompt_parts.append("- CHECK")
        prompt_parts.append("- CALL")
        prompt_parts.append("- RAISE_TO X (where X is the total amount you are raising to, e.g., RAISE_TO 500)")
        prompt_parts.append("Example: RAISE_TO 1000")
        prompt_parts.append("Only provide the action. No other text or explanation.")
        
        return "\n".join(prompt_parts)
    except Exception as e:
        # Final fallback in case of any errors
        return f"""
You are an expert Texas Hold'em poker player named '{player_name}'. This is game ID: {game_id}.
You are Player {player_index_for_ai + 1}.

Due to technical issues, detailed game state information is not available: {str(e)}
Given the uncertainty, you should play conservatively.

--- Your Decision ---
Respond with your chosen action in ONE LINE, using ONE of the following formats:
- FOLD
- CHECK
- CALL
- RAISE_TO X (where X is the total amount you are raising to, e.g., RAISE_TO 500)

Example: FOLD
Only provide the action. No other text or explanation.
"""
