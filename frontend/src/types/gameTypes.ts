export interface PlayerActionRequest {
    player_id?: string; // For human player identification
    action_type: string; // "fold", "call", "check", "raise"
    amount?: number; // Total amount for a raise action
}

// NEW: Player Config
export interface PlayerConfig {
    name?: string;
    ai_type: string;
    stack?: number;
    gemini_model?: string; // Optional: specific Gemini model version
    gpt_model?: string; // Optional: specific GPT model version
}

export interface StartGameRequest {
    player_one_ai_type?: string;
    player_two_ai_type?: string;
    players?: PlayerConfig[]; // NEW
    human_player_index?: number | null; // Modified to allow null or undefined
    initial_stacks?: number[]; // Default stacks
    blinds?: number[]; // Default blinds
}

export interface GameStateResponse {
    game_id: string;
    status: boolean; // True if game is ongoing, False if hand/game is over
    player_count: number;
    button_index: number;
    actor_index?: number | null;
    stacks: number[];
    bets: number[];
    pot_total: number; // Calculated from bets
    board_cards: string[];
    player_hole_cards?: Record<number, string[]> | null; // Keyed by player_index
    player_names?: string[] | null; // Actual player names from game setup
    payoffs?: number[] | null;
    available_actions?: string[] | null; // e.g. ["fold", "check_or_call", "complete_bet_or_raise_to"]
    checking_or_calling_amount?: number | null;
    min_raise_to_amount?: number | null;
    max_raise_to_amount?: number | null;
    current_round_name?: string | null; // e.g. "PREFLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"
    last_action_details?: Record<string, any> | null; // Details of the last action taken
    error_message?: string | null;
    ai_message?: string | null; // AI thought/reasoning for chat panel
}

export interface PlayerState {
    index: number;
    name: string; // e.g., "Player 0 (dummy)" or "Human"
    stack: number;
    currentBet: number; // The amount this player has bet in the current round
    holeCards?: string[]; // Cards for this player, undefined if not known/shown to the observer
    isActor: boolean; // Is it this player's turn?
    isDealer: boolean; // Is this player the dealer?
    lastAction?: string; // Description of the last action, e.g., "bets 100", "folds"
    payoff?: number; // Optional: what they won/lost in the hand if it's over
}
