import sqlite3
import json
import os
from typing import Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), 'research_data.db')

class DBClient:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Experiments Table: Metadata about a specific run
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                config_json TEXT,  -- Stores config dump (agents, blinds, etc.)
                status TEXT
            )
        ''')

        # 2. Hands Table: Summary of each poker hand played
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hands (
                id TEXT PRIMARY KEY,
                experiment_id TEXT,
                hand_number INTEGER,
                board_cards TEXT, -- JSON array of cards
                pot_size INTEGER,
                winner_model TEXT, -- Name of the winning AI model
                winning_hand TEXT, -- e.g., "Full House"
                FOREIGN KEY(experiment_id) REFERENCES experiments(id)
            )
        ''')

        # 3. Actions Table: Every single move made by an AI
        # Critical for analyzing decision quality and bluffs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hand_id TEXT,
                round_name TEXT, -- PREFLOP, FLOP, TURN, RIVER
                player_model TEXT,
                action_type TEXT,
                amount INTEGER,
                reasoning_raw TEXT, -- The AI's full thought process
                input_tokens INTEGER,
                output_tokens INTEGER,
                cost_usd REAL,
                FOREIGN KEY(hand_id) REFERENCES hands(id)
            )
        ''')
        
        # 4. Agent Stats (Snapshot per hand or per experiment?)
        # Let's track running stack sizes per hand for graphs
        cursor.execute('''
             CREATE TABLE IF NOT EXISTS stack_history (
                hand_id TEXT,
                player_model TEXT,
                stack_start INTEGER,
                stack_end INTEGER,
                net_change INTEGER,
                FOREIGN KEY(hand_id) REFERENCES hands(id)
             )
        ''')

        conn.commit()
        conn.close()

    def create_experiment(self, experiment_id: str, config: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO experiments (id, config_json, status) VALUES (?, ?, ?)",
            (experiment_id, json.dumps(config), "RUNNING")
        )
        conn.commit()
        conn.close()

    def log_hand(self, hand_id: str, experiment_id: str, hand_number: int, board: list, pot: int, winner: str, hand_name: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO hands (id, experiment_id, hand_number, board_cards, pot_size, winner_model, winning_hand) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (hand_id, experiment_id, hand_number, json.dumps(board), pot, winner, hand_name)
        )
        conn.commit()
        conn.close()

    def log_action(self, hand_id: str, round_name: str, model: str, action: str, amount: int, reasoning: str, usage_stats: Dict = None):
        """
        Log an individual action.
        usage_stats optional dict with {input_tokens, output_tokens, cost}
        """
        usage_stats = usage_stats or {}
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            '''INSERT INTO actions 
            (hand_id, round_name, player_model, action_type, amount, reasoning_raw, input_tokens, output_tokens, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                hand_id, 
                round_name, 
                model, 
                action, 
                amount or 0, 
                reasoning, 
                usage_stats.get('input_tokens', 0), 
                usage_stats.get('output_tokens', 0), 
                usage_stats.get('cost', 0.0)
            )
        )
        conn.commit()
        conn.close()

    def log_stack_update(self, hand_id: str, model: str, start: int, end: int):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO stack_history (hand_id, player_model, stack_start, stack_end, net_change) VALUES (?, ?, ?, ?, ?)",
            (hand_id, model, start, end, end - start)
        )
        conn.commit()
        conn.close()
