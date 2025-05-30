from abc import ABC, abstractmethod
from pokerkit import State
from app.api.v1.poker_schemas import PlayerActionRequest # Adjusted import path

class AIPlayer(ABC):
    @abstractmethod
    async def get_action(self, pk_state: State, player_index: int, game_id: str, player_name: str) -> PlayerActionRequest:
        pass
