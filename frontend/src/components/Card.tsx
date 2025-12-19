import React from 'react';
import './Card.css';

interface CardProps {
    cardString?: string; // e.g. "As", "Td", "2h", "5c"
    hidden?: boolean;
    scale?: number; // Optional scaling factor
    isWinning?: boolean; // True if this card is part of the winning hand
    isDimmed?: boolean; // True if this card should be dimmed
}

const getSuitSVG = (suit: string) => {
    switch (suit.toLowerCase()) {
        case 'h': // Heart
            return (
                <svg viewBox="0 0 100 100" fill="currentColor" width="1em" height="1em">
                    <path d="M50 88.9L42.75 81.65C17 56.4 0 39.75 0 19.35C0 7.6 8.85 0 19.35 0C25.25 0 30.95 2.75 34.65 7.05L50 25.1L65.35 7.05C69.05 2.75 74.75 0 80.65 0C91.15 0 100 7.6 100 19.35C100 39.75 83 56.4 57.25 81.65L50 88.9Z" />
                </svg>
            );
        case 'd': // Diamond
            return (
                <svg viewBox="0 0 100 100" fill="currentColor" width="1em" height="1em">
                    <path d="M50 100L12.5 50L50 0L87.5 50L50 100Z" />
                </svg>
            );
        case 'c': // Club
            return (
                <svg viewBox="0 0 100 100" fill="currentColor" width="1em" height="1em">
                    <path d="M50 35C41.7 35 35 28.3 35 20C35 11.7 41.7 5 50 5C58.3 5 65 11.7 65 20C65 28.3 58.3 35 50 35ZM20 65C11.7 65 5 58.3 5 50C5 41.7 11.7 35 20 35C28.3 35 35 41.7 35 50C35 58.3 28.3 65 20 65ZM80 65C71.7 65 65 58.3 65 50C65 41.7 71.7 35 80 35C88.3 35 95 41.7 95 50C95 58.3 88.3 65 80 65ZM50 70C38.3 70 30 50 25 50C25 50 15 50 15 70C15 85 35 85 40 90L40 95L60 95L60 90C65 85 85 85 85 70C85 50 75 50 75 50C70 50 61.7 70 50 70Z" />
                </svg>
            );
        case 's': // Spade
        default:
            return (
                <svg viewBox="0 0 100 100" fill="currentColor" width="1em" height="1em">
                    <path d="M50 0C25 35 15 50 15 65C15 78.8 26.2 90 40 90C45 90 45 75 50 75C55 75 55 90 60 90C73.8 90 85 78.8 85 65C85 50 75 35 50 0ZM50 75L40 95L60 95L50 75Z" />
                </svg>
            );
    }
};

const Card: React.FC<CardProps> = ({ cardString, hidden, scale = 1, isWinning = false, isDimmed = false }) => {
    if (hidden) {
        return (
            <div className={`poker-card hidden ${isDimmed ? 'dimmed' : ''}`} style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
                <div className="card-pattern"></div>
            </div>
        );
    }

    if (!cardString || cardString.length < 2) {
        return <div className="poker-card placeholder">?</div>;
    }

    const rank = cardString.slice(0, -1); // 'A', 'T', '10', '2'
    const suitChar = cardString.slice(-1); // 's', 'd', 'h', 'c'

    // Determine Color
    const isRed = ['h', 'd'].includes(suitChar.toLowerCase());
    const colorClass = isRed ? 'red' : 'black';

    // SVG Suit
    const suitSVG = getSuitSVG(suitChar);

    // Handle 'T' for Ten usually means '10' in display? Or Keep 'T'? 
    // PokerKit often returns "T", "J", "Q", "K", "A". 
    // Usually 10 is better displayed as 10.
    const displayRank = rank === 'T' ? '10' : rank.toUpperCase();

    return (
        <div
            className={`poker-card ${colorClass} ${isWinning ? 'winner' : ''} ${isDimmed ? 'dimmed' : ''}`}
            style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}
        >
            <div className="card-top-left">
                <span className="rank-text">{displayRank}</span>
                <div className="suit-icon">{suitSVG}</div>
            </div>
            <div className="card-center-suit">
                {suitSVG}
            </div>
            <div className="card-bottom-right">
                <span className="rank-text">{displayRank}</span>
                <div className="suit-icon">{suitSVG}</div>
            </div>
        </div>
    );
};

export default Card;
