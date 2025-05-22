import React from 'react';

interface GameControlsProps {
    onNextAiTurn: () => void;
    onResetGame: () => void;
    gameId: string | null;
    isGameOver: boolean;
    isLoading: boolean;
}

const GameControls: React.FC<GameControlsProps> = ({ 
    onNextAiTurn, 
    onResetGame, 
    gameId, 
    isGameOver, 
    isLoading 
}) => {
    return (
        <div className="game-controls">
            <button 
                onClick={onNextAiTurn} 
                disabled={!gameId || isGameOver || isLoading}
            >
                {isLoading ? 'Processing...' : 'Next AI Turn'}
            </button>
            <button 
                onClick={onResetGame} 
                disabled={isLoading} // Prevent reset while another action is loading
            >
                New Game / Reset
            </button>
        </div>
    );
};

export default GameControls;
