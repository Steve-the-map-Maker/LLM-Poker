import axios from 'axios';
import { GameStateResponse, StartGameRequest, PlayerActionRequest, PlayerConfig } from '../types/gameTypes';

// API URL - change this for production deployment
// API URL - configurable for production
const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1/game";

export const startGameApi = async (players: PlayerConfig[], blinds?: number[]): Promise<GameStateResponse> => {
    console.log("startGameApi called with players:", players, "blinds:", blinds);

    // Find human index
    let human_player_index: number | null = null;
    players.forEach((p, index) => {
        if (p.ai_type === 'human') {
            human_player_index = index;
        }
    });

    const payload: StartGameRequest = {
        players: players,
        human_player_index: human_player_index,
        blinds: blinds // Add blinds to payload
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

export const playerActionApi = async (gameId: string, actionRequest: PlayerActionRequest): Promise<GameStateResponse> => {
    console.log("playerActionApi called with gameId:", gameId, "action:", actionRequest);
    try {
        const response = await axios.post(`${API_BASE_URL}/${gameId}/action`, actionRequest);
        console.log("playerActionApi response:", response.data);
        return response.data;
    } catch (error) {
        console.error(`Error submitting player action for gameId ${gameId}:`, error);
        if (axios.isAxiosError(error) && error.response) {
            console.error("Error response data:", error.response.data);
            throw new Error(error.response.data.detail || "Failed to submit player action");
        }
        throw new Error("Failed to submit player action due to an unexpected error.");
    }
};

export const startNextHandApi = async (gameId: string): Promise<GameStateResponse> => {
    console.log("startNextHandApi called with gameId:", gameId);
    try {
        const response = await axios.post(`${API_BASE_URL}/${gameId}/next_hand`);
        console.log("startNextHandApi response:", response.data);
        return response.data;
    } catch (error) {
        console.error(`Error starting next hand for gameId ${gameId}:`, error);
        if (axios.isAxiosError(error) && error.response) {
            console.error("Error response data:", error.response.data);
            throw new Error(error.response.data.detail || "Failed to start next hand");
        }
        throw new Error("Failed to start next hand due to an unexpected error.");
    }
};
