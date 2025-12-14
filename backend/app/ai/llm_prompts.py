import pokerkit
from typing import List

def format_poker_state_for_llm(pk_state: pokerkit.State, player_index_for_ai: int, game_id: str, player_name: str, history: List[str]) -> str:
    """
    Formats the current poker game state into a detailed text prompt for an LLM.
    Uses PokerKit State object to extract comprehensive game information.
    """
    try:
        # --- Concise Context ---
        # Basic identity and game info
        prompt_parts = [
            f"Game: Texas Hold'em No Limit. ID: {game_id}.",
            f"You are Player {player_index_for_ai + 1} ('{player_name}').",
            "",
            "=== CRITICAL POKER RULES ===",
            "1. If 'To Call: 0' → You can CHECK for FREE! NEVER fold when checking is free!",
            "2. Big Blind pre-flop: If no one raised, you CHECK (it's already paid).",
            "3. Pre-flop with any two cards: CALL small raises, don't fold easily.",
            "4. Position matters: Later position = more information = play more hands.",
            "",
            "=== YOUR STRATEGY (Loose-Aggressive) ===",
            "- Play MANY hands, not just premium hands",
            "- RAISE often with good hands (pairs, suited connectors, broadway)",
            "- CALL with marginal hands rather than folding",
            "- Bluff occasionally, especially in position",
            "- ONLY FOLD when facing a big raise with nothing",
            "",
        ]
        
        # --- State Snapshot ---
        # Hand & Board
        try:
            hole_cards = pk_state.hole_cards[player_index_for_ai]
            cards_list = []
            if hole_cards:
                for c in hole_cards:
                    if hasattr(c, 'rank'):
                        cards_list.append(f"{c.rank.value}{c.suit.value}")
                    else:
                        cards_list.append(str(c))
            
            my_hand = " ".join(cards_list) if cards_list else "Unknown"
        except Exception as e:
            print(f"Error formatting hand: {e}")
            my_hand = "Unknown"
        
        try:
            board = pk_state.board_cards
            board_str = " ".join([f"{c.rank.value}{c.suit.value}" for c in board]) if board else "None (Pre-flop)"
        except: board_str = "None"
        
        street_map = {0: "Pre-flop", 1: "Flop", 2: "Turn", 3: "River"}
        round_name = street_map.get(getattr(pk_state, 'street_index', -1), "Unknown")
        
        prompt_parts.append(f"=== CURRENT SITUATION ===")
        prompt_parts.append(f"Street: {round_name}")
        prompt_parts.append(f"Board: {board_str}")
        prompt_parts.append(f"Your Hand: {my_hand}")

        # Chips & Pot
        try:
            pot = getattr(pk_state, 'total_pot_amount', 0)
            stack = pk_state.stacks[player_index_for_ai]
            to_call = getattr(pk_state, 'checking_or_calling_amount', 0)
            prompt_parts.append(f"Pot: {pot}. Your Stack: {stack}. To Call: {to_call}.")
            
            # Add decision hint based on situation
            if to_call == 0:
                prompt_parts.append(">>> TO CALL IS 0! You can CHECK for free. DO NOT FOLD!")
            elif to_call < pot * 0.3:
                prompt_parts.append(f">>> Small bet to call ({to_call}). Good pot odds to CALL.")
        except:
            prompt_parts.append("Chip counts unavailable.")

        # --- Recent History (Last 5 actions) ---
        prompt_parts.append("")
        prompt_parts.append("Recent Actions:")
        try:
            ops = getattr(pk_state, 'operations', [])
            recent_ops = ops[-5:] if ops else []
            if not recent_ops:
                prompt_parts.append("- None yet")
            else:
                for op in recent_ops:
                    p_idx = getattr(op, 'player_index', -1)
                    p_label = "You" if p_idx == player_index_for_ai else f"P{p_idx+1}"
                    op_class_name = type(op).__name__
                    details = "acts"
                    
                    if "Fold" in op_class_name: 
                        details = "folds"
                    elif "Check" in op_class_name or "Call" in op_class_name: 
                        details = f"checks/calls {getattr(op, 'amount', 0)}"
                    elif "Raise" in op_class_name or "Bet" in op_class_name or "Completion" in op_class_name: 
                        details = f"raises to {getattr(op, 'amount', 0)}"
                    elif "Blind" in op_class_name or "Ante" in op_class_name:
                        details = f"posts {getattr(op, 'amount', 0)}"
                    
                    prompt_parts.append(f"- {p_label} {details}")
        except Exception as e:
            print(f"History parsing error: {e}")
            prompt_parts.append("- (history unavailable)")

        # --- Valid Actions ---
        prompt_parts.append("")
        prompt_parts.append("=== YOUR OPTIONS ===")
        actions = []
        if pk_state.can_fold(): actions.append("FOLD (only if facing big bet)")
        if pk_state.can_check_or_call(): 
            if to_call == 0:
                actions.append("CHECK ← RECOMMENDED (it's free!)")
            else:
                actions.append("CALL")
        if pk_state.can_complete_bet_or_raise_to():
             min_r = getattr(pk_state, 'min_completion_betting_or_raising_to_amount', 0)
             actions.append(f"RAISE_TO {min_r}+ (show strength)")
        
        prompt_parts.append(", ".join(actions) if actions else "FOLD")

        # --- Instruction ---
        prompt_parts.append("")
        prompt_parts.append("=== YOUR DECISION ===")
        prompt_parts.append("Respond with EXACTLY one: FOLD, CHECK, CALL, or RAISE_TO <amount>")
        
        return "\n".join(prompt_parts)
    except Exception as e:
        # Final fallback - STILL BE AGGRESSIVE
        print(f"Prompt generation exception: {e}")
        return (
            f"You are a LOOSE-AGGRESSIVE professional poker player named '{player_name}'. Game ID: {game_id}.\n"
            f"You are Player {player_index_for_ai + 1}.\n\n"
            "ROLE: You bluff often, call with weak hands, and raise frequently.\n"
            "STRATEGY: NEVER fold preflop. Call or raise. Be unpredictable.\n\n"
            "--- Your Decision ---\n"
            "Respond with EXACTLY one action:\n"
            "- CALL\n"
            "- RAISE_TO 300\n\n"
            "DO NOT FOLD. Pick CALL or RAISE_TO."
        )
