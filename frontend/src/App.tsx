import React, { useState, useEffect } from 'react';
import LLMSelector from './components/LLMSelector';
import PokerTable from './components/PokerTable';
import GameControls from './components/GameControls';
import ActionControls from './components/ActionControls';
import ChatPanel, { ChatMessage } from './components/ChatPanel';
import LoadingModal from './components/LoadingModal';
import { startGameApi, advanceAiTurnApi, playerActionApi, startNextHandApi } from './services/gameApi';
import { GameStateResponse, PlayerActionRequest, PlayerConfig } from './types/gameTypes';
import './App.css';

const App: React.FC = () => {
    const [gameId, setGameId] = useState<string | null>(null);
    const [gameState, setGameState] = useState<GameStateResponse | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [humanPlayerIndex, setHumanPlayerIndex] = useState<number | null>(null);
    const [autoPlay, setAutoPlay] = useState<boolean>(true);
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
    const [messageId, setMessageId] = useState<number>(0);
    const [showLoadingModal, setShowLoadingModal] = useState<boolean>(false);
    const [backendReady, setBackendReady] = useState<boolean>(false);

    // Pre-warm backend on page load
    useEffect(() => {
        const warmupBackend = async () => {
            try {
                const API_BASE = process.env.REACT_APP_API_URL?.replace('/api/v1/game', '') || 'http://localhost:8000';
                const response = await fetch(`${API_BASE}/health`);
                if (response.ok) {
                    setBackendReady(true);
                    console.log('Backend warmed up successfully');
                }
            } catch (error) {
                console.log('Backend warming up...');
                // Retry after 2 seconds
                setTimeout(warmupBackend, 2000);
            }
        };
        warmupBackend();
    }, []);

    // Auto-play Effect
    useEffect(() => {
        let timeoutId: ReturnType<typeof setTimeout>;

        if (autoPlay && gameId && gameState && !isLoading && !error) {
            // Case 1: Hand Over -> STOP auto-play so user can review results
            if (gameState.status === false) {
                // Pause auto-play when hand ends
                setAutoPlay(false);
                return; // Don't auto-advance to next hand
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
        setShowLoadingModal(true);
        setError(null);
        // keep autoPlay as is (default true)
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
        setShowLoadingModal(false);
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
        setChatMessages([]);
    };

    const handleSendChatMessage = async (message: string) => {
        if (!gameId || !gameState) return;

        // Add human message to chat
        const humanMessage: ChatMessage = {
            id: messageId,
            sender: 'You',
            message: message,
            timestamp: new Date(),
            type: 'human'
        };
        setChatMessages(prev => [...prev, humanMessage]);
        setMessageId(prev => prev + 1);

        // Call backend API to get AI response to chat
        try {
            const response = await fetch(`http://localhost:8000/api/v1/game/${gameId}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.ai_response) {
                    const aiResponse: ChatMessage = {
                        id: messageId + 1,
                        sender: data.ai_name || 'AI',
                        message: data.ai_response,
                        timestamp: new Date(),
                        type: 'ai'
                    };
                    setChatMessages(prev => [...prev, aiResponse]);
                    setMessageId(prev => prev + 2);
                }
            }
        } catch (error) {
            console.error('Chat API error:', error);
        }
    };

    const isHumanTurn = gameState?.status === true && gameState.actor_index === humanPlayerIndex && humanPlayerIndex !== null;
    const humanPlayerStack = humanPlayerIndex !== null && gameState?.stacks ? gameState.stacks[humanPlayerIndex] : 0;

    // Capture AI messages from game state
    useEffect(() => {
        // Get AI player name from last action details
        const getPlayerName = (playerIndex: number | undefined): string => {
            if (playerIndex === undefined) return 'AI';
            if (playerIndex === humanPlayerIndex) return 'You';
            // Use actual player names from game state, or fallback to defaults
            if (gameState?.player_names && playerIndex < gameState.player_names.length) {
                return gameState.player_names[playerIndex];
            }
            const aiNamesByIndex = ['GeminiPro', 'StarDust', 'CosmicAce', 'NebulaKing', 'AstroBluffer', 'DumbBot'];
            return aiNamesByIndex[playerIndex] || `AI ${playerIndex + 1}`;
        };

        // Helper to clean action keywords from AI message
        const cleanAiMessage = (msg: string): string => {
            if (!msg) return msg;
            // Remove action keywords at the end (FOLD, CHECK, CALL, RAISE_TO XXX)
            return msg
                .replace(/\s*(FOLD|CHECK|CALL|RAISE_TO\s*\d+)\s*$/i, '')
                .trim();
        };

        if (gameState?.ai_message && gameState?.last_action_details) {
            const aiPlayerIndex = gameState.last_action_details.player_index;
            // Skip if this is the human player
            if (aiPlayerIndex === humanPlayerIndex) return;

            const aiName = getPlayerName(aiPlayerIndex);
            const cleanedMessage = cleanAiMessage(gameState.ai_message);

            // Only add if there's actual content after cleaning
            if (cleanedMessage && cleanedMessage.length > 3) {
                const newMessage: ChatMessage = {
                    id: messageId,
                    sender: aiName,
                    message: cleanedMessage,
                    timestamp: new Date(),
                    type: 'ai'
                };
                setChatMessages(prev => [...prev, newMessage]);
                setMessageId(prev => prev + 1);
            }
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
            {/* Loading Modal */}
            <LoadingModal
                isVisible={showLoadingModal}
                message={backendReady ? "Starting game..." : "Waking up the server..."}
            />

            {!gameId && (
                <header className="App-header">
                    <h1>LLM Poker Arena</h1>
                    {!backendReady && (
                        <p style={{
                            color: '#ffa726',
                            fontSize: '0.9rem',
                            animation: 'pulse 1.5s infinite'
                        }}>
                            ⏳ Connecting to server...
                        </p>
                    )}
                </header>
            )}
            <main>
                {error && <p className="error-message">Error: {error}</p>}

                {!gameId ? (
                    <LLMSelector onStartGame={handleStartGame} isLoading={isLoading} />
                ) : (
                    <div className="game-container" style={{ height: 'calc(100vh - 20px)' }}>
                        {/* LEFT SIDEBAR - Controls */}
                        <div className="left-sidebar">
                            <div className="sidebar-section">
                                <h3 className="sidebar-title">🎮 Game Controls</h3>
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

                            {isHumanTurn && gameState && (
                                <div className="sidebar-section">
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
                                        potTotal={gameState.pot_total || 0}
                                    />
                                </div>
                            )}
                        </div>

                        {/* CENTER - Game Table */}
                        <div className="game-area">
                            <PokerTable
                                gameState={gameState}
                                humanPlayerIndex={humanPlayerIndex}
                                isAiThinking={isLoading && gameState?.status === true && gameState?.actor_index !== humanPlayerIndex}
                            />

                            {/* Game Over Overlay */}
                            {gameState && gameState.error_message && (gameState.error_message.startsWith('🏆') || gameState.error_message.startsWith('🎲')) && (
                                <div className="game-over-overlay">
                                    <div className="game-over-modal">
                                        <div className="game-over-emoji">
                                            {gameState.error_message.includes('CONGRATULATIONS') ? '🎉' : '🏆'}
                                        </div>
                                        <h2 className="game-over-title">
                                            {gameState.error_message.includes('CONGRATULATIONS') ? 'YOU WON!' : 'GAME OVER'}
                                        </h2>
                                        <p className="game-over-message">
                                            {gameState.error_message.replace('🏆 CONGRATULATIONS! ', '').replace('🏆 GAME OVER! ', '')}
                                        </p>
                                        <div className="game-over-buttons">
                                            <button
                                                onClick={handleResetGame}
                                                className="game-over-btn new-game-btn"
                                            >
                                                🎮 New Game
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* RIGHT SIDEBAR - Chat */}
                        <ChatPanel
                            messages={chatMessages}
                            gameId={gameId}
                            onSendMessage={handleSendChatMessage}
                        />
                    </div>
                )}
            </main>
        </div>
    );
};

export default App;
