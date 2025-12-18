import React, { useEffect, useState } from 'react';
import { GameStateResponse, PlayerState } from '../types/gameTypes';
import PlayerDisplay from './PlayerDisplay';
import Card from './Card'; // Import Card component
import './PokerTable.css'; // Ensure we have a CSS file for table specifcs if not already

interface PokerTableProps {
    gameState: GameStateResponse | null;
    humanPlayerIndex?: number | null;
    isAiThinking?: boolean;
}

const PokerTable: React.FC<PokerTableProps> = ({ gameState, humanPlayerIndex, isAiThinking }) => {
    if (!gameState) {
        return <div className="poker-table loading">Waiting for game state...</div>;
    }

    // Helper to transform GameStateResponse player data to PlayerState for PlayerDisplay
    const getPlayerState = (playerIndex: number): PlayerState => {
        const isActor = gameState.actor_index === playerIndex;
        // Use actual player name from API, or generate default
        let playerName = `Player ${playerIndex + 1}`;
        if (gameState.player_names && gameState.player_names[playerIndex]) {
            playerName = gameState.player_names[playerIndex];
        } else if (playerIndex === humanPlayerIndex) {
            playerName = "You";
        }

        let holeCards: string[] | undefined = undefined;
        if (gameState.player_hole_cards && gameState.player_hole_cards[playerIndex]) {
            holeCards = gameState.player_hole_cards[playerIndex];
        }

        // Show cards if the game is over (status is false or payoffs exist)
        const showCards = !gameState.status || !!gameState.payoffs;

        let lastActionString = "N/A";
        if (gameState.last_action_details && gameState.last_action_details.player_index === playerIndex) {
            lastActionString = `${gameState.last_action_details.action_type}`;
            if (gameState.last_action_details.amount) {
                lastActionString += ` ${gameState.last_action_details.amount}`;
            }
        }

        // Check if player has folded from the server's tracking
        const isFolded = gameState.players_folded?.[playerIndex] ?? false;

        return {
            index: playerIndex,
            name: playerName,
            stack: gameState.stacks[playerIndex],
            currentBet: gameState.bets[playerIndex],
            holeCards: holeCards,
            isActor: isActor,
            isDealer: gameState.button_index === playerIndex,
            lastAction: lastActionString, // Simplified, App.tsx might manage a more detailed log
            isFolded: isFolded,
            payoff: gameState.payoffs ? gameState.payoffs[playerIndex] : undefined,
        };
    };

    // Generate states for all players
    const playerStates: PlayerState[] = [];
    if (gameState.player_count) {
        for (let i = 0; i < gameState.player_count; i++) {
            playerStates.push(getPlayerState(i));
        }
    }

    // Winner message logic
    let gameStatusMessage = "Game in progress";
    if (!gameState.status || gameState.payoffs) {
        gameStatusMessage = "Hand Over";
        if (gameState.payoffs) {
            // Find winners (players with positive payoff or max stack increase?)
            // Actually payoffs in PokerKit usually represent the change or the amount awarded?
            // If it's the amount awarded from pot, any > 0 is a winner (or split).
            const winners: string[] = [];
            gameState.payoffs.forEach((amount, index) => {
                if (amount > 0) {
                    winners.push(playerStates[index].name);
                }
            });

            if (winners.length > 0) {
                gameStatusMessage += ` - Winner: ${winners.join(', ')}`;
            } else {
                // Could be a push return or purely chips pushing automation?
                // Usually there is a winner.
            }
        }
    }

    // Helper to calculate visual seat position
    // We want the Human player to always be at seat-0 (Bottom Center)
    const getVisualSeatIndex = (playerIndex: number, totalPlayers: number) => {
        const totalSeats = 6; // We defined 6 positions in CSS

        // If we want to strictly enforce Hero at bottom:
        if (humanPlayerIndex !== null && humanPlayerIndex !== undefined) {
            // Shift so human is at 0
            // logic: (actual - human + total) % total
            // This rotates the table so human is 0. 
            // However, we might have fewer players than seats. 
            // Let's just create a relative offset.
            const offset = humanPlayerIndex;
            const relativeIndex = (playerIndex - offset + totalPlayers) % totalPlayers;

            // Now map relativeIndex (0..N-1) to Seat Positions (0..5)
            // seat-0 is bottom.
            // If 2 players: 0 (Bot), 3 (Top) -> Head's up layout
            // If 3 players: 0 (Bot), 2 (TopLeft), 4 (TopRight)? Or 0, 2, 4?

            // Simple mapping for now:
            if (totalPlayers === 2) {
                return relativeIndex === 0 ? 0 : 3; // Bot, Top
            } else if (totalPlayers === 3) {
                // 0, 2, 4 (Triangle)
                const map = [0, 2, 4];
                return map[relativeIndex];
            } else if (totalPlayers <= 6) {
                // Just fill nicely? Or just standard rotation.
                // If standard rotation based on 6 seats:
                const seatDiff = Math.floor(6 / totalPlayers);
                // This might be tricky. Let's just use the raw relative index mapped to closest seat triggers.
                // Actually, let's just rotate them simply.
                // (playerIndex - humanIndex + 6) % 6 works if full table.
                // But with 3 players at indices 0,1,2...

                // Let's stick to a simple shift for N=totalPlayers
                // We need to map 0..N-1 to 0..5

                // Hardcoded maps for best aesthetics
                const seatMaps: { [key: number]: number[] } = {
                    2: [0, 3],
                    3: [0, 2, 4],
                    4: [0, 1, 3, 5], // Bot, BotLeft, Top, BotRight
                    5: [0, 1, 2, 3, 5],
                    6: [0, 1, 2, 3, 4, 5]
                };

                const map = seatMaps[totalPlayers] || [0, 1, 2, 3, 4, 5]; // fallback
                return map[relativeIndex];
            }
        }

        // Spectator mode (humanIndex null) -> Just fill 0..N
        const seatMaps: { [key: number]: number[] } = {
            2: [0, 3],
            3: [0, 2, 4],
            4: [0, 1, 3, 5],
            5: [0, 1, 2, 3, 5],
            6: [0, 1, 2, 3, 4, 5]
        };
        const map = seatMaps[totalPlayers] || [0, 1, 2, 3, 4, 5];
        return map[playerIndex];
    };

    return (
        <div className="poker-table-container">
            {/* The Felt Table */}
            <div className="poker-felt">
                <div className="table-center-info">
                    <h4>Pot: ${gameState.pot_total}</h4>
                    <div>{gameState.current_round_name}</div>
                    {isAiThinking && (
                        <div className="ai-thinking-indicator">
                            <div className="thinking-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <span className="thinking-text">AI is thinking...</span>
                        </div>
                    )}
                </div>

                <div className="community-cards-area">
                    {/* Render up to 5 card slots, filled or placeholder */}
                    {[0, 1, 2, 3, 4].map(idx => {
                        const cardStr = gameState.board_cards[idx];
                        if (cardStr) {
                            return <Card key={idx} cardString={cardStr} />;
                        } else {
                            return <div key={idx} className="card-placeholder" />;
                        }
                    })}
                </div>

                {gameState.error_message && <div style={{ color: 'red', background: 'rgba(0,0,0,0.8)', padding: '5px' }}>Error: {gameState.error_message}</div>}
            </div>

            {/* Absolute Seats Layer */}
            <div className="seats-layer">
                {playerStates.map((player, i) => {
                    const visualSeat = getVisualSeatIndex(player.index, gameState.player_count);
                    const hasCards = !!(gameState.player_hole_cards && gameState.player_hole_cards[player.index]);
                    const isHuman = player.index === humanPlayerIndex;
                    const gameOver = !gameState.status || !!gameState.payoffs;

                    // Human always sees their own cards. AI cards only shown when game over.
                    const shouldShowCards = hasCards && (isHuman || gameOver);

                    return (
                        <div key={player.index} className={`seat seat-${visualSeat}`}>
                            <PlayerDisplay
                                player={player}
                                isDealer={gameState.button_index === player.index}
                                showCards={shouldShowCards}
                            />
                        </div>
                    );
                })}
            </div>

            {/* Hand Result Overlay */}
            {(!gameState.status || gameState.payoffs) && (
                <div className="hand-result-overlay">
                    {gameStatusMessage}
                </div>
            )}
        </div>
    );
};

export default PokerTable;
