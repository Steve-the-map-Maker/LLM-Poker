import React, { useState, useEffect } from 'react';
import LLMSelector from './components/LLMSelector';
import PokerTable from './components/PokerTable';
import GameControls from './components/GameControls';
import ActionControls from './components/ActionControls'; // Import ActionControls
import { startGameApi, advanceAiTurnApi, playerActionApi } from './services/gameApi'; 
import { GameStateResponse, PlayerActionRequest } from './types/gameTypes'; // Import PlayerActionRequest
import './App.css';

const App: React.FC = () => {
    const [gameId, setGameId] = useState<string | null>(null);
    const [gameState, setGameState] = useState<GameStateResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [humanPlayerIndex, setHumanPlayerIndex] = useState<number | null>(null);

    const handleStartGame = async (player1Type: string, player2Type: string) => {
        setIsLoading(true);
        setError(null);
        try {
            let determinedHumanPlayerIndex: number | null = null;
            if (player1Type.toLowerCase() === 'human') {
                determinedHumanPlayerIndex = 0;
            } else if (player2Type.toLowerCase() === 'human') {
                determinedHumanPlayerIndex = 1;
            }
            setHumanPlayerIndex(determinedHumanPlayerIndex);

            const data = await startGameApi(player1Type, player2Type);
            setGameState(data);
            setGameId(data.game_id);
        } catch (err: any) {
            setError(err.message || "Failed to start game.");
            console.error(err);
        }
        setIsLoading(false);
    };

    const handlePlayerAction = async (actionType: string, amount?: number) => {
        if (!gameId || humanPlayerIndex === null || !gameState || gameState.actor_index !== humanPlayerIndex) {
            setError("Cannot perform action: Not human's turn or game not active.");
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            const actionRequest: PlayerActionRequest = { action_type: actionType };
            if (amount !== undefined) {
                actionRequest.amount = amount;
            }
            const data = await playerActionApi(gameId, actionRequest); // Use the actual API call
            setGameState(data); // Update game state with the response
        } catch (err: any) {
            setError(err.message || "Failed to perform player action.");
            console.error(err);
        } finally {
            setIsLoading(false); // Ensure loading is set to false after action attempt
        }
    };

    const handleNextAiTurn = async () => {
        if (!gameId || (gameState && !gameState.status)) return;
        if (gameState && gameState.actor_index === humanPlayerIndex && humanPlayerIndex !== null) {
            setError("It's the human player's turn. AI turn cannot be advanced.");
            return;
        }
        setIsLoading(true);
        setError(null);
        try {
            const data = await advanceAiTurnApi(gameId);
            setGameState(data);
        } catch (err: any) {
            setError(err.message || "Failed to advance AI turn.");
            console.error(err);
        }
        setIsLoading(false);
    };

    const handleResetGame = () => {
        setGameId(null);
        setGameState(null);
        setError(null);
        setHumanPlayerIndex(null);
    };
    
    const isHumanTurn = gameState?.status === true && gameState.actor_index === humanPlayerIndex && humanPlayerIndex !== null;
    const humanPlayerStack = humanPlayerIndex !== null && gameState?.stacks ? gameState.stacks[humanPlayerIndex] : 0;

    return (
        <div className="App">
            <header className="App-header">
                <h1>LLM Poker Arena</h1>
            </header>
            <main>
                {error && <p className="error-message">Error: {error}</p>}

                {!gameId ? (
                    <LLMSelector onStartGame={handleStartGame} isLoading={isLoading} />
                ) : (
                    <>
                        <PokerTable gameState={gameState} humanPlayerIndex={humanPlayerIndex} />
                        {isHumanTurn && gameState && (
                            <ActionControls
                                gameId={gameId}
                                humanPlayerIndex={humanPlayerIndex}
                                isHumanTurn={isHumanTurn}
                                availableActions={gameState.available_actions || []}
                                checkingOrCallingAmount={gameState.checking_or_calling_amount || 0}
                                minRaiseToAmount={gameState.min_raise_to_amount || 0}
                                maxRaiseToAmount={gameState.max_raise_to_amount || humanPlayerStack}
                                playerStack={humanPlayerStack}
                                onPlayerAction={handlePlayerAction}
                                isLoading={isLoading}
                            />
                        )}
                        <GameControls 
                            onNextAiTurn={handleNextAiTurn} 
                            onResetGame={handleResetGame} 
                            gameId={gameId} 
                            isGameOver={gameState ? !gameState.status : false} 
                            isLoading={isLoading}
                            isHumanPlayer={humanPlayerIndex !== null}
                            isHumanTurn={isHumanTurn}
                        />
                    </>
                )}
            </main>
        </div>
    );
};

export default App;
