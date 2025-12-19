import React from 'react';
import { PlayerState } from '../types/gameTypes';
import Card from './Card';
import ChipStack from './ChipStack';
import './PlayerDisplay.css';

interface PlayerDisplayProps {
    player?: PlayerState;
    isDealer: boolean;
    showCards: boolean;
    winningCards?: string[] | null; // Cards involved in the winning hand
}

const PlayerDisplay: React.FC<PlayerDisplayProps> = ({ player, isDealer, showCards, winningCards }) => {
    if (!player) {
        return <div className="player-display loading">Loading...</div>;
    }

    const isWinner = player.payoff !== undefined && player.payoff > 0;
    // Use the isFolded prop from the server tracking, fallback to lastAction parsing for backwards compatibility
    const isFolded = player.isFolded ?? player.lastAction?.toLowerCase().includes('fold');

    // Determine Cards to Display
    let cardsToRender: React.ReactNode = null;

    if (!isFolded) {
        if (player.holeCards && player.holeCards.length > 0 && showCards) {
            // Show actual cards
            cardsToRender = (
                <>
                    {player.holeCards.map((cardStr, idx) => {
                        const isWinningCard = winningCards?.includes(cardStr);
                        // Dim cards if we have a winning hand defined AND this card is not part of it
                        const isDimmed = !!(winningCards && winningCards.length > 0 && !isWinningCard);
                        return <Card key={idx} cardString={cardStr} scale={0.6} isWinning={isWinningCard} isDimmed={isDimmed} />;
                    })}
                </>
            );
        } else {
            // Show hidden backs (assuming 2 for Hold'em)
            cardsToRender = (
                <>
                    {/* Hidden cards can be dimmed if game is over and someone else won, but tricky to know context here.
                        Usually hidden cards just stay hidden. */}
                    <Card hidden scale={0.6} />
                    <Card hidden scale={0.6} />
                </>
            );
        }
    }

    return (
        <div className={`player-display ${player.isActor ? 'active' : ''} ${isFolded ? 'folded' : ''}`}>
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

            {/* Current Round Bet - Now with visual chips! */}
            {player.currentBet > 0 && (
                <div className="player-bet">
                    <ChipStack amount={player.currentBet} size="small" />
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
