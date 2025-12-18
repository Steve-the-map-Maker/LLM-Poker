from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.api.v1.poker_schemas import StartGameRequest, GameStateResponse, PlayerActionRequest
from app.services.game_service import GameService
from app.core.poker_game_manager import PokerGameManager

router = APIRouter()

# Dependency for game manager (singleton-like for the app lifecycle)
# In a real app, you might manage this with FastAPI's app state or a more robust DI system.
poker_game_manager = PokerGameManager()
game_service_instance = GameService(poker_game_manager) # Instantiate GameService once

def get_game_service():
    return game_service_instance # Return the single instance

@router.post("/start", response_model=GameStateResponse)
async def start_new_game(
    start_request: StartGameRequest,
    game_service: GameService = Depends(get_game_service)
):
    """
    Initializes a new PokerKit game. 
    Invokes `game_service.create_new_game_instance`.
    """
    try:
        game_state = game_service.create_new_game_instance(start_request)
        return game_state
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=500, detail=f"Failed to start game: {str(e)}")

@router.get("/{game_id}/state", response_model=GameStateResponse)
async def get_game_state(
    game_id: str, 
    human_player_index: Optional[int] = None, # Optional query param for human context
    game_service: GameService = Depends(get_game_service)
):
    """
    Retrieves the current state of the specified game. 
    Invokes `game_service.get_game_state`.
    """
    game_state = game_service.get_game_state(game_id, human_player_index)
    if not game_state:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_state

@router.post("/{game_id}/action", response_model=GameStateResponse)
async def player_action(
    game_id: str, 
    action_request: PlayerActionRequest, # PlayerActionRequest from poker_schemas
    game_service: GameService = Depends(get_game_service)
):
    """
    Processes a player's action. If the actor is human, this endpoint is used.
    Invokes `game_service.process_human_action`.
    """
    current_pk_state = game_service.game_manager.get_game_state(game_id)
    if not current_pk_state:
        raise HTTPException(status_code=404, detail="Game not found")

    if not current_pk_state.status:
        raise HTTPException(status_code=400, detail="Game is over. No actions can be taken.")

    actor_index = current_pk_state.actor_index
    if actor_index is None:
        raise HTTPException(status_code=400, detail="No player is currently set to act.")

    # Check if the current actor is human based on stored identities
    player_identities = game_service.game_player_identities.get(game_id)
    if not player_identities or player_identities.get(actor_index) != "human":
        # This endpoint should only be called for human actions.
        # If it's an AI's turn, advance_ai_turn should be used.
        raise HTTPException(
            status_code=403,
            detail=f"Player {actor_index} is not a human player or identities not found. Use advance_ai_turn for AI."
        )
    
    human_player_index = actor_index # Confirmed: current actor is human

    try:
        # Pass the confirmed human_player_index to the service method
        updated_game_state = game_service.process_human_action(game_id, action_request, human_player_index)
        
        if updated_game_state.error_message:
            # Only treat as error if it's NOT a game over message
            is_game_over_message = updated_game_state.error_message.startswith("🏆") or updated_game_state.error_message.startswith("🎲")
            if not is_game_over_message:
                # The service layer might return a state with an error message for invalid actions
                raise HTTPException(status_code=400, detail=updated_game_state.error_message)
        return updated_game_state
    except ValueError as e:
        # Catch specific ValueErrors from service layer if not already in response model
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the exception e for debugging
        print(f"Unhandled exception in /action for game {game_id}, player {human_player_index}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing action: {str(e)}")

@router.post("/{game_id}/advance_ai_turn", response_model=GameStateResponse)
async def advance_ai_turn(
    game_id: str, 
    game_service: GameService = Depends(get_game_service)
):
    """
    If it's an AI's turn, fetches the AI's move and applies it. 
    Invokes `game_service.run_ai_vs_ai_game_turn`.
    """
    try:
        # The service method is now async
        game_state = await game_service.run_ai_vs_ai_game_turn(game_id)
        # Only treat as error if it's NOT a game over message
        # Game over messages start with 🏆 or 🎲 and are normal end states
        if game_state.error_message:
            is_game_over_message = game_state.error_message.startswith("🏆") or game_state.error_message.startswith("🎲")
            if not is_game_over_message:
                # This is an actual error, not a game over
                raise HTTPException(status_code=400, detail=game_state.error_message)
        return game_state
    except ValueError as e: # Catch specific ValueErrors if service raises them directly
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log the exception e for debugging
        print(f"Unhandled exception in /advance_ai_turn for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to advance AI turn: {str(e)}")
@router.post("/{game_id}/next_hand", response_model=GameStateResponse)
async def start_next_hand(
    game_id: str,
    game_service: GameService = Depends(get_game_service)
):
    """
    Starts the next hand for an existing game.
    Invokes `game_service.start_next_hand`.
    """
    try:
        game_state = game_service.start_next_hand(game_id)
        return game_state
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unhandled exception in /next_hand for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start next hand: {str(e)}")

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    ai_response: str
    ai_name: str

@router.post("/{game_id}/chat", response_model=ChatResponse)
async def chat_with_ai(
    game_id: str,
    chat_request: ChatRequest,
    game_service: GameService = Depends(get_game_service)
):
    """
    Send a chat message and get an AI response.
    Uses a random AI player from the game to respond.
    """
    import random
    try:
        import google.generativeai as genai
        from app.config import settings
        
        # Get player names and pick a random AI
        player_names = game_service.game_player_names.get(game_id, ["AI"])
        player_identities = game_service.game_player_identities.get(game_id, {})
        
        # Find AI players (non-human)
        ai_players = [(i, name) for i, name in enumerate(player_names) 
                      if player_identities.get(i) != "human"]
        
        if not ai_players:
            ai_name = "AI"
        else:
            _, ai_name = random.choice(ai_players)
        
        # Get custom prompt for this AI if available
        custom_prompts = game_service.game_player_custom_prompts.get(game_id, {})
        personality = custom_prompts.get(0, "You are a confident, trash-talking poker player.")
        
        # Generate response using Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            prompt = f"""You are {ai_name}, a poker AI with this personality: {personality}

The human player just said: "{chat_request.message}"

Respond with a short, witty trash-talk response (1-2 sentences max). Be confident and playful. Don't mention specific cards or game state."""
            
            response = await model.generate_content_async(prompt)
            ai_response = response.text.strip()
        else:
            ai_response = "Nice try, but I don't tilt! 😎"
        
        return ChatResponse(ai_response=ai_response, ai_name=ai_name)
        
    except Exception as e:
        print(f"Chat error: {e}")
        return ChatResponse(
            ai_response="Keep talking while I take your chips! 💸",
            ai_name="AI"
        )
