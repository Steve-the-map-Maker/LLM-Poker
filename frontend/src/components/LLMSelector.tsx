import React, { useState } from 'react';

interface LLMSelectorProps {
    onStartGame: (player1Type: string, player2Type: string) => void;
    isLoading: boolean;
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ onStartGame, isLoading }) => {
    const [player1Type, setPlayer1Type] = useState<string>("dummy");
    const [player2Type, setPlayer2Type] = useState<string>("dummy");

    const playerOptions = ["human", "dummy", "gpt", "gemini"];

    const handleStart = () => {
        onStartGame(player1Type, player2Type);
    };

    return (
        <div>
            <h2>Select Players</h2>
            <div>
                <label htmlFor="player1Type">Player 1: </label>
                <select 
                    id="player1Type" 
                    value={player1Type} 
                    onChange={(e) => setPlayer1Type(e.target.value)}
                    disabled={isLoading}
                >
                    {playerOptions.map(type => <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>)}
                </select>
            </div>
            <div>
                <label htmlFor="player2Type">Player 2: </label>
                <select 
                    id="player2Type" 
                    value={player2Type} 
                    onChange={(e) => setPlayer2Type(e.target.value)}
                    disabled={isLoading}
                >
                    {playerOptions.map(type => <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>)}
                </select>
            </div>
            <button onClick={handleStart} disabled={isLoading}>
                {isLoading ? 'Starting Game...' : 'Start Game'}
            </button>
        </div>
    );
};

export default LLMSelector;
