import React, { useState, useEffect } from 'react';
import LLMSelector from './components/LLMSelector';
import PokerTable from './components/PokerTable';
import GameControls from './components/GameControls';
import { startGameApi, advanceAiTurnApi, getGameStateApi } from './services/gameApi';
import { GameStateResponse } from './types/gameTypes';
import './App.css'; // Assuming you will create a basic App.css for styling

const App: React.FC = () => {
    const [gameId, setGameId] = useState<string | null>(null);
    const [gameState, setGameState] = useState<GameStateResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    // Optional: If you want to try and load a game state if a gameId is in localStorage
    // useEffect(() => {
    //     const storedGameId = localStorage.getItem('pokerGameId');
    //     if (storedGameId) {
    //         setGameId(storedGameId);
    //         // Potentially fetch game state here if you want to resume
    //         // handleGetGameState(storedGameId);
    //     }
    // }, []);

    const handleStartGame = async (ai1: string, ai2: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await startGameApi(ai1, ai2);
            setGameState(data);
            setGameId(data.game_id);
            // localStorage.setItem('pokerGameId', data.game_id); // Optional: persist gameId
        } catch (err: any) {
            setError(err.message || "Failed to start game.");
            console.error(err);
        }
        setIsLoading(false);
    };

    const handleNextAiTurn = async () => {
        if (!gameId || (gameState && !gameState.status)) return; // Game over or no gameId
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

    // Example function if you wanted to manually refresh/get state
    // const handleGetGameState = async (currentId: string) => {
    //     setIsLoading(true);
    //     setError(null);
    //     try {
    //         const data = await getGameStateApi(currentId);
    //         setGameState(data);
    //     } catch (err: any) {
    //         setError(err.message || "Failed to fetch game state.");
    //         console.error(err);
    //     }
    //     setIsLoading(false);
    // };

    const handleResetGame = () => {
        setGameId(null);
        setGameState(null);
        setError(null);
        // localStorage.removeItem('pokerGameId'); // Optional: clear persisted gameId
    };

    return (
        <div className="App">
            <header className="App-header">
                <h1>LLM Poker Arena</h1>
            </header>
            <main>
                {error && <p className="error-message">Error: {error}</p>}
                {isLoading && <p className="loading-message">Loading...</p>}

                {!gameId ? (
                    <LLMSelector onStartGame={handleStartGame} isLoading={isLoading} />
                ) : (
                    <>
                        <PokerTable gameState={gameState} />
                        <GameControls 
                            onNextAiTurn={handleNextAiTurn} 
                            onResetGame={handleResetGame} 
                            gameId={gameId} 
                            isGameOver={gameState ? !gameState.status : false} 
                            isLoading={isLoading} 
                        />
                        {/* Button to manually refresh state - useful for debugging */}
                        {/* <button onClick={() => gameId && handleGetGameState(gameId)} disabled={isLoading}>Refresh Game State</button> */}
                    </>
                )}
            </main>
        </div>
    );
};

export default App;
