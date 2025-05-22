import React from 'react';
import { GameStateResponse, PlayerState } from '../types/gameTypes';
import PlayerDisplay from './PlayerDisplay';

interface PokerTableProps {
    gameState: GameStateResponse | null;
    humanPlayerIndex?: number | null; // Optional: to highlight human player or adjust display
}

const PokerTable: React.FC<PokerTableProps> = ({ gameState, humanPlayerIndex }) => {
    if (!gameState) {
        return <div className="poker-table loading">Waiting for game state...</div>;
    }

    // Helper to transform GameStateResponse player data to PlayerState for PlayerDisplay
    const getPlayerState = (playerIndex: number): PlayerState => {
        const isActor = gameState.actor_index === playerIndex;
        // Determine player name
        let playerName = `Player ${playerIndex}`;
        if (playerIndex === humanPlayerIndex) {
            playerName = `Human (Player ${playerIndex})`;
        } else {
            // Assuming player_one_ai_type and player_two_ai_type might be available in future gameState
            // For now, just use a generic AI name or rely on App.tsx to pass more specific names if needed.
            playerName = `AI Opponent (Player ${playerIndex})`; 
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

        return {
            index: playerIndex,
            name: playerName, 
            stack: gameState.stacks[playerIndex],
            currentBet: gameState.bets[playerIndex],
            holeCards: holeCards,
            isActor: isActor,
            isDealer: gameState.button_index === playerIndex,
            lastAction: lastActionString, // Simplified, App.tsx might manage a more detailed log
            payoff: gameState.payoffs ? gameState.payoffs[playerIndex] : undefined,
        };
    };

    const playerOneState = getPlayerState(0);
    const playerTwoState = getPlayerState(1);

    // Determine if cards should be shown for each player
    // For LLM vs LLM, we might always want to show cards if available, or only at showdown.
    // For now, show if game is over or if player_hole_cards are present (which they should be for spectation)
    const showPlayerOneCards = !!(gameState.player_hole_cards && gameState.player_hole_cards[0]) && (!gameState.status || !!gameState.payoffs);
    const showPlayerTwoCards = !!(gameState.player_hole_cards && gameState.player_hole_cards[1]) && (!gameState.status || !!gameState.payoffs);

    let gameStatusMessage = "Game in progress";
    if (!gameState.status || gameState.payoffs) {
        gameStatusMessage = "Hand Over";
        if (gameState.payoffs) {
            if (gameState.payoffs[0] > 0) gameStatusMessage += ` - ${playerOneState.name} wins!`;
            else if (gameState.payoffs[1] > 0) gameStatusMessage += ` - ${playerTwoState.name} wins!`;
            else gameStatusMessage += " - It's a tie/push!";
        }
    }

    return (
        <div className="poker-table">
            <h3>{gameStatusMessage}</h3>
            <div className="players-container">
                <PlayerDisplay 
                    player={playerOneState} 
                    isDealer={gameState.button_index === 0} 
                    showCards={showPlayerOneCards}
                />
                <PlayerDisplay 
                    player={playerTwoState} 
                    isDealer={gameState.button_index === 1} 
                    showCards={showPlayerTwoCards}
                />
            </div>
            <div className="table-info">
                <h4>Community Cards: {gameState.board_cards.join(' ') || 'None'}</h4>
                <h4>Pot: {gameState.pot_total}</h4>
                <h4>Current Round: {gameState.current_round_name || 'N/A'}</h4>
                {gameState.last_action_details && (
                    <h4>
                        Last Action: Player {gameState.last_action_details.player_index} - {gameState.last_action_details.action_type}
                        {gameState.last_action_details.amount ? ` to ${gameState.last_action_details.amount}` : ''}
                    </h4>
                )}
                 {gameState.error_message && <p style={{color: 'red'}}>Error: {gameState.error_message}</p>}
            </div>
        </div>
    );
};

export default PokerTable;
