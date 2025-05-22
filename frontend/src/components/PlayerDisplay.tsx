import React from 'react';
import { PlayerState } from '../types/gameTypes';

interface PlayerDisplayProps {
    player?: PlayerState; // Make player optional to handle loading states
    isDealer: boolean;
    showCards: boolean; // True if game over or human player's own cards
    // Removed playerIndex as it should be part of PlayerState or derivable
}

const PlayerDisplay: React.FC<PlayerDisplayProps> = ({ player, isDealer, showCards }) => {
    if (!player) {
        return <div className="player-display loading">Loading player...</div>;
    }

    const cardDisplay = (cards?: string[]) => {
        if (!cards || cards.length === 0) return "No cards";
        if (showCards) {
            return cards.join(' ');
        }
        return cards.map(() => '??').join(' ');
    };

    return (
        <div className={`player-display ${player.isActor ? 'actor' : ''}`}>
            <h4>{player.name} {isDealer ? '(D)' : ''}</h4>
            <p>Stack: {player.stack}</p>
            <p>Current Bet: {player.currentBet}</p>
            <p>Cards: {cardDisplay(player.holeCards)}</p>
            {player.lastAction && <p>Last Action: {player.lastAction}</p>}
            {player.payoff !== undefined && <p>Payoff: {player.payoff}</p>}
        </div>
    );
};

export default PlayerDisplay;
