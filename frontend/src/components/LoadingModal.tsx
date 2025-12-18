import React, { useEffect, useState } from 'react';
import './LoadingModal.css';

interface LoadingModalProps {
    isVisible: boolean;
    message?: string;
}

const LoadingModal: React.FC<LoadingModalProps> = ({ isVisible, message = "Starting game..." }) => {
    const [pokerFact, setPokerFact] = useState<string>("Shuffling the deck...");
    const [progress, setProgress] = useState<number>(0);

    useEffect(() => {
        if (isVisible) {
            // Fetch poker fact from backend
            const fetchFact = async () => {
                try {
                    const API_BASE = process.env.REACT_APP_API_URL?.replace('/api/v1/game', '') || 'http://localhost:8000';
                    const response = await fetch(`${API_BASE}/poker-fact`);
                    if (response.ok) {
                        const data = await response.json();
                        setPokerFact(data.fact);
                    }
                } catch (error) {
                    // Use fallback fact
                    setPokerFact("The best hand in poker is a Royal Flush! 👑");
                }
            };
            fetchFact();

            // Animate progress bar
            setProgress(0);
            const interval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(interval);
                        return 90; // Cap at 90% until actually done
                    }
                    return prev + Math.random() * 15;
                });
            }, 500);

            return () => clearInterval(interval);
        }
    }, [isVisible]);

    if (!isVisible) return null;

    return (
        <div className="loading-modal-overlay">
            <div className="loading-modal">
                <div className="loading-cards">
                    <span className="card-icon">🂡</span>
                    <span className="card-icon">🂱</span>
                    <span className="card-icon">🃁</span>
                    <span className="card-icon">🃑</span>
                </div>

                <h2 className="loading-title">{message}</h2>

                <div className="progress-container">
                    <div
                        className="progress-bar"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                <div className="poker-fact">
                    <span className="fact-icon">💡</span>
                    <p>{pokerFact}</p>
                </div>

                <div className="loading-spinner">
                    <div className="chip-spinner">🎰</div>
                </div>
            </div>
        </div>
    );
};

export default LoadingModal;
