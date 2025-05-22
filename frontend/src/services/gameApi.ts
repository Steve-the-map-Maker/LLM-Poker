import axios from 'axios';
import { GameStateResponse, StartGameRequest } from '../types/gameTypes';

const API_BASE_URL = "http://localhost:8000/api/v1/game";

export const startGameApi = async (playerOneAiType: string, playerTwoAiType: string): Promise<GameStateResponse> => {
    console.log("startGameApi called with:", playerOneAiType, playerTwoAiType);
    const payload: StartGameRequest = {
        player_one_ai_type: playerOneAiType,
        player_two_ai_type: playerTwoAiType,
        human_player_index: null, // Explicitly null as per current phase
        // initial_stacks and blinds will use backend defaults
    };
    try {
        const response = await axios.post(`${API_BASE_URL}/start`, payload);
        console.log("startGameApi response:", response.data);
        return response.data;
    } catch (error) {
        console.error("Error starting game:", error);
        if (axios.isAxiosError(error) && error.response) {
            console.error("Error response data:", error.response.data);
            throw new Error(error.response.data.detail || "Failed to start game");
        }
        throw new Error("Failed to start game due to an unexpected error.");
    }
};

export const getGameStateApi = async (gameId: string): Promise<GameStateResponse> => {
    console.log("getGameStateApi called with gameId:", gameId);
    try {
        const response = await axios.get(`${API_BASE_URL}/${gameId}/state`);
        console.log("getGameStateApi response:", response.data);
        return response.data;
    } catch (error) {
        console.error(`Error fetching game state for gameId ${gameId}:`, error);
        if (axios.isAxiosError(error) && error.response) {
            console.error("Error response data:", error.response.data);
            throw new Error(error.response.data.detail || "Failed to fetch game state");
        }
        throw new Error("Failed to fetch game state due to an unexpected error.");
    }
};

export const advanceAiTurnApi = async (gameId: string): Promise<GameStateResponse> => {
    console.log("advanceAiTurnApi called with gameId:", gameId);
    try {
        const response = await axios.post(`${API_BASE_URL}/${gameId}/advance_ai_turn`);
        console.log("advanceAiTurnApi response:", response.data);
        return response.data;
    } catch (error) {
        console.error(`Error advancing AI turn for gameId ${gameId}:`, error);
        if (axios.isAxiosError(error) && error.response) {
            console.error("Error response data:", error.response.data);
            throw new Error(error.response.data.detail || "Failed to advance AI turn");
        }
        throw new Error("Failed to advance AI turn due to an unexpected error.");
    }
};
