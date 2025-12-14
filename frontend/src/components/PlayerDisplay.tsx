import React from 'react';
import { PlayerState } from '../types/gameTypes';
import Card from './Card';
import './PlayerDisplay.css';

interface PlayerDisplayProps {
    player?: PlayerState;
    isDealer: boolean;
    showCards: boolean;
}

const PlayerDisplay: React.FC<PlayerDisplayProps> = ({ player, isDealer, showCards }) => {
    if (!player) {
        return <div className="player-display loading">Loading...</div>;
    }

    const isWinner = player.payoff !== undefined && player.payoff > 0;
    const isFolded = player.lastAction?.toLowerCase().includes('fold');

    // Determine Cards to Display
    let cardsToRender: React.ReactNode = null;

    if (!isFolded) {
        if (player.holeCards && player.holeCards.length > 0 && showCards) {
            // Show actual cards
            cardsToRender = (
                <>
                    {player.holeCards.map((cardStr, idx) => (
                        <Card key={idx} cardString={cardStr} scale={0.6} />
                    ))}
                </>
            );
        } else {
            // Show hidden backs (assuming 2 for Hold'em)
            cardsToRender = (
                <>
                    <Card hidden scale={0.6} />
                    <Card hidden scale={0.6} />
                </>
            );
        }
    }

    return (
        <div className={`player-display ${player.isActor ? 'active' : ''}`}>
            {/* Action Bubble (e.g. "Check", "Raise 500") */}
            {player.lastAction && (
                <div className="last-action-bubble">
                    {player.lastAction}
                </div>
            )}

            {/* Floating Cards (Top) */}
            <div className="player-cards">
                {cardsToRender}
            </div>

            {/* Avatar Circle */}
            <div className={`player-avatar ${player.isActor ? 'active' : ''} ${isWinner ? 'winner' : ''}`}>
                <span className="avatar-initial">{player.name.charAt(0)}</span>
                {isDealer && <div className="dealer-button">D</div>}
            </div>

            {/* Info Box */}
            <div className="player-info">
                <p className="player-name" title={player.name}>{player.name}</p>
                <p className="player-stack">${player.stack}</p>
            </div>

            {/* Current Round Bet */}
            {player.currentBet > 0 && (
                <div className="player-bet">
                    <span className="chip-icon"></span>
                    {player.currentBet}
                </div>
            )}

            {/* Payoff Animation Placeholder */}
            {player.payoff !== undefined && player.payoff !== 0 && (
                <div style={{
                    position: 'absolute',
                    top: '-60px',
                    color: player.payoff > 0 ? '#4CAF50' : '#ff4444',
                    fontWeight: 'bold',
                    textShadow: '0 0 5px black',
                    zIndex: 20
                }}>
                    {player.payoff > 0 ? '+' : ''}{player.payoff}
                </div>
            )}
        </div>
    );
};

export default PlayerDisplay;
