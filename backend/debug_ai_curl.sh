#!/bin/bash
# Start a game with Human vs Gemini
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/game/start \
  -H "Content-Type: application/json" \
  -d '{
    "players": [
        {"name": "Human", "ai_type": "human"},
        {"name": "Bot", "ai_type": "gemini"}
    ],
    "human_player_index": 0
}')

GAME_ID=$(echo $RESPONSE | grep -o '"game_id":"[^"]*"' | cut -d'"' -f4)
echo "Created Game: $GAME_ID"

# Advance AI turn (Player 1 is Gemini)
# We might need to act as human first (Preflop, Button 0 -> SB 0, BB 1).
# If 2 players: P0 (Btn/SB), P1 (BB).
# P0 acts first. P0 is Human.
# So we need to process human action (Call/Fold/Raise) to pass turn to AI.
# Let's Call.

echo "Human (P0) Calling..."
curl -s -X POST http://localhost:8000/api/v1/game/$GAME_ID/action \
  -H "Content-Type: application/json" \
  -d '{"action_type": "call", "amount": 0}'

echo -e "\n\nAdvancing AI Turn..."
curl -s -X POST http://localhost:8000/api/v1/game/$GAME_ID/advance_ai_turn
