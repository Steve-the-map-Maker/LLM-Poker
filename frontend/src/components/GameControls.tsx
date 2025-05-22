import React from 'react';

interface GameControlsProps {
    onNextAiTurn: () => void;
    onResetGame: () => void;
    gameId: string | null;
    isGameOver: boolean;
    isLoading: boolean;
    isHumanPlayer?: boolean; // Added: Optional prop to indicate if a human is playing
    isHumanTurn?: boolean;   // Added: Optional prop to indicate if it's the human's turn
}

const GameControls: React.FC<GameControlsProps> = ({ 
    onNextAiTurn, 
    onResetGame, 
    gameId, 
    isGameOver, 
    isLoading,
    isHumanPlayer, // Destructure new prop
    isHumanTurn    // Destructure new prop
}) => {
    return (
        <div className="game-controls">
            <button 
                onClick={onNextAiTurn} 
                // Disable if no game, game over, loading, or if it's a human player's turn
                disabled={!gameId || isGameOver || isLoading || (isHumanPlayer && isHumanTurn)}
            >
                {isLoading ? 'Processing...' : (isHumanPlayer && isHumanTurn) ? 'Waiting for Your Action' : 'Next AI Turn'}
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
