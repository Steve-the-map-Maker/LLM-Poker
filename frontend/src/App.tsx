import React, { useState, useEffect } from 'react';
import LLMSelector from './components/LLMSelector';
import PokerTable from './components/PokerTable';
import GameControls from './components/GameControls';
import ActionControls from './components/ActionControls';
import ChatPanel, { ChatMessage } from './components/ChatPanel';
import { startGameApi, advanceAiTurnApi, playerActionApi, startNextHandApi } from './services/gameApi';
import { GameStateResponse, PlayerActionRequest, PlayerConfig } from './types/gameTypes';
import './App.css';

const App: React.FC = () => {
    const [gameId, setGameId] = useState<string | null>(null);
    const [gameState, setGameState] = useState<GameStateResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [humanPlayerIndex, setHumanPlayerIndex] = useState<number | null>(null);
    const [autoPlay, setAutoPlay] = useState<boolean>(false);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [messageId, setMessageId] = useState<number>(0);

    // Auto-play Effect
    useEffect(() => {
        let timeoutId: ReturnType<typeof setTimeout>;

        if (autoPlay && gameId && gameState && !isLoading && !error) {
            // Case 1: Game Over -> Start Next Hand (after delay)
            if (gameState.status === false) {
                timeoutId = setTimeout(() => {
                    handleNextHand();
                }, 2000); // 2 second delay between hands
            }
            // Case 2: Game Active -> Play Turn
            else {
                // Check if it's NOT human turn
                const isHumanTurn = gameState.actor_index === humanPlayerIndex && humanPlayerIndex !== null;

                if (!isHumanTurn) {
                    // Determine a delay. Faster for AI vs AI, slightly slower if watching? 
                    // Let's go fast: 500ms
                    timeoutId = setTimeout(() => {
                        handleNextAiTurn();
                    }, 500);
                }
                // If it is human turn, we wait.
            }
        }

        return () => clearTimeout(timeoutId);
    }, [autoPlay, gameId, gameState, isLoading, error, humanPlayerIndex]);


    const handleStartGame = async (players: PlayerConfig[], blinds: number[]) => {
        setIsLoading(true);
        setError(null);
        setAutoPlay(false); // Reset auto-play on new game
        try {
            let determinedHumanPlayerIndex: number | null = null;
            // Find first human
            players.forEach((p, index) => {
                if (p.ai_type === 'human' && determinedHumanPlayerIndex === null) {
                    determinedHumanPlayerIndex = index;
                }
            });
            setHumanPlayerIndex(determinedHumanPlayerIndex);

            const data = await startGameApi(players, blinds);
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
            setAutoPlay(false); // Stop auto-play on error
        } finally {
            setIsLoading(false); // Ensure loading is set to false after action attempt
        }
    };

    const handleNextAiTurn = async () => {
        if (!gameId || (gameState && !gameState.status)) {
            // Game over logic handled in Effect if AutoPlay is on. 
            // If manual click, we should allow it? No, manual click for "Next Turn" shouldn't work if game over.
            return;
        }
        if (gameState && gameState.actor_index === humanPlayerIndex && humanPlayerIndex !== null) {
            return;
        }
        setIsLoading(true);
        try {
            const data = await advanceAiTurnApi(gameId);
            setGameState(data);
            // Don't stop autoPlay here anymore on game over, let the Effect handle transition to next hand.
        } catch (err: any) {
            setError(err.message || "Failed to advance AI turn.");
            console.error(err);
            setAutoPlay(false); // Stop on error
        }
        setIsLoading(false);
    };

    const handleNextHand = async () => {
        if (!gameId) return;
        setIsLoading(true);
        setError(null);
        try {
            const data = await startNextHandApi(gameId);
            setGameState(data);
        } catch (err: any) {
            setError(err.message || "Failed to start next hand.");
            console.error(err);
            setAutoPlay(false);
        }
        setIsLoading(false);
    }

    const handleResetGame = () => {
        setGameId(null);
        setGameState(null);
        setError(null);
        setHumanPlayerIndex(null);
        setAutoPlay(false);
    };

    const isHumanTurn = gameState?.status === true && gameState.actor_index === humanPlayerIndex && humanPlayerIndex !== null;
    const humanPlayerStack = humanPlayerIndex !== null && gameState?.stacks ? gameState.stacks[humanPlayerIndex] : 0;

    // Capture AI messages from game state
    useEffect(() => {
        // Get AI player name from last action details
        const getPlayerName = (playerIndex: number | undefined): string => {
            if (playerIndex === undefined) return 'AI';
            if (playerIndex === humanPlayerIndex) return 'You';
            // AI names match by player index (consistent with LLMSelector)
            const aiNamesByIndex = ['GeminiPro', 'StarDust', 'CosmicAce', 'NebulaKing', 'AstroBluffer', 'DumbBot'];
            return aiNamesByIndex[playerIndex] || `AI ${playerIndex + 1}`;
        };

        if (gameState?.ai_message && gameState?.last_action_details) {
            const aiPlayerIndex = gameState.last_action_details.player_index;
            const aiName = getPlayerName(aiPlayerIndex);
            const newMessage: ChatMessage = {
                id: messageId,
                sender: aiName,
                message: gameState.ai_message,
                timestamp: new Date(),
                type: 'ai'
            };
            setChatMessages(prev => [...prev, newMessage]);
            setMessageId(prev => prev + 1);
        }
        // Add action messages for visibility
        if (gameState?.last_action_details) {
            const details = gameState.last_action_details;
            const playerName = getPlayerName(details.player_index);
            let actionText = details.action || details.action_type || 'acted';
            if (details.amount || details.amount_called || details.amount_raised_to) {
                actionText += ` $${details.amount || details.amount_called || details.amount_raised_to}`;
            }
            const actionMessage: ChatMessage = {
                id: messageId + 1,
                sender: playerName,
                message: actionText,
                timestamp: new Date(),
                type: 'action'
            };
            setChatMessages(prev => [...prev, actionMessage]);
            setMessageId(prev => prev + 2);
        }
    }, [gameState?.ai_message, gameState?.last_action_details]);

    return (
        <div className="App">
            {!gameId && (
                <header className="App-header">
                    <h1>LLM Poker Arena</h1>
                </header>
            )}
            <main>
                {error && <p className="error-message">Error: {error}</p>}

                {!gameId ? (
                    <LLMSelector onStartGame={handleStartGame} isLoading={isLoading} />
                ) : (
                    <div className="game-container" style={{ height: 'calc(100vh - 20px)' }}>
                        <div className="game-area">
                            <PokerTable
                                gameState={gameState}
                                humanPlayerIndex={humanPlayerIndex}
                                isAiThinking={isLoading && gameState?.status === true && gameState?.actor_index !== humanPlayerIndex}
                            />
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
                                onNextHand={handleNextHand}
                                gameId={gameId}
                                isGameOver={gameState ? !gameState.status : false}
                                isLoading={isLoading}
                                isHumanPlayer={humanPlayerIndex !== null}
                                isHumanTurn={isHumanTurn}
                                autoPlay={autoPlay}
                                onToggleAutoPlay={() => setAutoPlay(!autoPlay)}
                            />
                        </div>
                        <ChatPanel messages={chatMessages} />
                    </div>
                )}
            </main>
        </div>
    );
};

export default App;
