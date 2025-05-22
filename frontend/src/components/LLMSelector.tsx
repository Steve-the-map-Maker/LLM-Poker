import React, { useState } from 'react';

interface LLMSelectorProps {
    onStartGame: (ai1: string, ai2: string) => void;
    isLoading: boolean;
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ onStartGame, isLoading }) => {
    const [player1Ai, setPlayer1Ai] = useState<string>("dummy");
    const [player2Ai, setPlayer2Ai] = useState<string>("dummy");

    const aiOptions = ["dummy", "gpt", "gemini"]; // Or fetch from a config/API later

    const handleStart = () => {
        onStartGame(player1Ai, player2Ai);
    };

    return (
        <div>
            <h2>Select LLM Opponents</h2>
            <div>
                <label htmlFor="player1Ai">Player 1 AI: </label>
                <select 
                    id="player1Ai" 
                    value={player1Ai} 
                    onChange={(e) => setPlayer1Ai(e.target.value)}
                    disabled={isLoading}
                >
                    {aiOptions.map(ai => <option key={ai} value={ai}>{ai.toUpperCase()}</option>)}
                </select>
            </div>
            <div>
                <label htmlFor="player2Ai">Player 2 AI: </label>
                <select 
                    id="player2Ai" 
                    value={player2Ai} 
                    onChange={(e) => setPlayer2Ai(e.target.value)}
                    disabled={isLoading}
                >
                    {aiOptions.map(ai => <option key={ai} value={ai}>{ai.toUpperCase()}</option>)}
                </select>
            </div>
            <button onClick={handleStart} disabled={isLoading}>
                {isLoading ? 'Starting Game...' : 'Start Game'}
            </button>
        </div>
    );
};

export default LLMSelector;
