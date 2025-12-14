import React from 'react';

interface GameControlsProps {
    onNextAiTurn: () => void;
    onResetGame: () => void;
    onNextHand: () => void;     // NEW
    gameId: string | null;
    isGameOver: boolean;
    isLoading: boolean;
    isHumanPlayer?: boolean;
    isHumanTurn?: boolean;
    autoPlay: boolean;
    onToggleAutoPlay: () => void;
}

const GameControls: React.FC<GameControlsProps> = ({
    onNextAiTurn,
    onResetGame,
    onNextHand,      // Destructure
    gameId,
    isGameOver,
    isLoading,
    isHumanPlayer,
    isHumanTurn,
    autoPlay,
    onToggleAutoPlay
}) => {
    return (
        <div className="game-controls">
            {!isGameOver && (
                <button
                    className={`auto-play-btn ${autoPlay ? 'active' : ''}`}
                    onClick={onToggleAutoPlay}
                    disabled={!gameId || isGameOver}
                    style={{ backgroundColor: autoPlay ? '#ffc107' : '', color: autoPlay ? '#000' : '' }}
                >
                    {autoPlay ? 'Stop Auto-Play' : 'Start Auto-Play'}
                </button>
            )}

            {isGameOver ? (
                // Show Next Hand button if game is over (and valid gameId exists)
                <button
                    onClick={onNextHand}
                    disabled={!gameId || isLoading}
                    className="action-btn call-btn" // Reusing styling
                    style={{ backgroundColor: '#28a745', color: 'white', fontWeight: 'bold' }}
                >
                    Start Next Hand
                </button>
            ) : (
                <button
                    onClick={onNextAiTurn}
                    // Disable if no game, game over, loading, or if it's a human player's turn
                    disabled={!gameId || isGameOver || isLoading || (isHumanPlayer && isHumanTurn) || autoPlay}
                >
                    {isLoading ? 'Processing...' : (isHumanPlayer && isHumanTurn) ? 'Waiting for Your Action' : 'Next AI Turn'}
                </button>
            )}

            <button
                onClick={onResetGame}
                disabled={isLoading}
            >
                Reset / New Game
            </button>
        </div>
    );
};

export default GameControls;
