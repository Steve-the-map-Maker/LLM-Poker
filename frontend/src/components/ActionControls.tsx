import React, { useState, useEffect } from 'react';
import './ActionControls.css';

interface ActionControlsProps {
  gameId: string | null;
  humanPlayerIndex: number | null;
  isHumanTurn: boolean;
  availableActions: string[];
  checkingOrCallingAmount: number;
  minRaiseToAmount: number;
  maxRaiseToAmount: number;
  playerStack: number;
  onPlayerAction: (actionType: string, amount?: number) => void;
  isLoading: boolean;
  potTotal?: number;
}

const ActionControls: React.FC<ActionControlsProps> = ({
  gameId,
  humanPlayerIndex,
  isHumanTurn,
  availableActions,
  checkingOrCallingAmount,
  minRaiseToAmount,
  maxRaiseToAmount,
  playerStack,
  onPlayerAction,
  isLoading,
  potTotal = 0,
}) => {
  const [raiseAmount, setRaiseAmount] = useState<number>(minRaiseToAmount);

  useEffect(() => {
    setRaiseAmount(minRaiseToAmount > 0 ? minRaiseToAmount : 0);
  }, [minRaiseToAmount]);

  if (!isHumanTurn || !gameId || humanPlayerIndex === null || availableActions.length === 0) {
    return null;
  }

  const canFold = availableActions.includes('fold');
  const isCheckOrCallAvailable = availableActions.includes('check_or_call');
  const canCheck = isCheckOrCallAvailable && checkingOrCallingAmount === 0;
  const canCall = isCheckOrCallAvailable && checkingOrCallingAmount > 0;
  const canBet = availableActions.includes('bet') || (availableActions.includes('complete_bet_or_raise_to') && checkingOrCallingAmount === 0);
  const canRaise = availableActions.includes('raise') || (availableActions.includes('complete_bet_or_raise_to') && checkingOrCallingAmount > 0);

  const handleFold = () => onPlayerAction('fold');
  const handleCheck = () => onPlayerAction('check');
  const handleCall = () => onPlayerAction('call');
  const handleBet = () => {
    if (raiseAmount >= minRaiseToAmount && raiseAmount <= maxRaiseToAmount) {
      onPlayerAction('bet', raiseAmount);
    }
  };
  const handleRaise = () => {
    if (raiseAmount >= minRaiseToAmount && raiseAmount <= maxRaiseToAmount) {
      onPlayerAction('raise', raiseAmount);
    }
  };

  const handleRaiseAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    setRaiseAmount(isNaN(value) ? 0 : value);
  };

  // Quick bet calculations
  const halfPot = Math.max(minRaiseToAmount, Math.floor(potTotal / 2));
  const fullPot = Math.max(minRaiseToAmount, potTotal);
  const twoPot = Math.min(maxRaiseToAmount, potTotal * 2);

  const setQuickBet = (amount: number) => {
    const clampedAmount = Math.min(Math.max(amount, minRaiseToAmount), maxRaiseToAmount);
    setRaiseAmount(clampedAmount);
  };

  return (
    <div className="action-controls">
      <h4>🎯 Your Turn</h4>

      {/* Main action buttons */}
      <div className="action-buttons-row">
        {canFold && (
          <button className="action-btn fold" onClick={handleFold} disabled={isLoading}>
            ❌ Fold
          </button>
        )}
        {canCheck && (
          <button className="action-btn check" onClick={handleCheck} disabled={isLoading}>
            ✓ Check
          </button>
        )}
        {canCall && (
          <button className="action-btn call" onClick={handleCall} disabled={isLoading}>
            📞 Call ${checkingOrCallingAmount}
          </button>
        )}
        {(canBet || canRaise) && (
          <button
            className={`action-btn ${canBet ? 'bet' : 'raise'}`}
            onClick={canBet ? handleBet : handleRaise}
            disabled={isLoading || raiseAmount < minRaiseToAmount || raiseAmount > maxRaiseToAmount}
          >
            💰 {canBet ? 'Bet' : 'Raise'} ${raiseAmount}
          </button>
        )}
        {(canBet || canRaise) && (
          <button
            className="action-btn all-in"
            onClick={() => onPlayerAction(canBet ? 'bet' : 'raise', maxRaiseToAmount)}
            disabled={isLoading}
          >
            🔥 All-In ${maxRaiseToAmount}
          </button>
        )}
      </div>

      {/* Raise controls */}
      {(canBet || canRaise) && (
        <div className="raise-controls">
          {/* Quick bet buttons */}
          <div className="quick-bet-buttons">
            <button className="quick-bet-btn" onClick={() => setQuickBet(halfPot)}>½ Pot</button>
            <button className="quick-bet-btn" onClick={() => setQuickBet(fullPot)}>Pot</button>
            <button className="quick-bet-btn" onClick={() => setQuickBet(twoPot)}>2× Pot</button>
          </div>

          {/* Amount input */}
          <div className="amount-input-group">
            <input
              type="number"
              id="raiseAmount"
              value={raiseAmount}
              onChange={handleRaiseAmountChange}
              min={minRaiseToAmount}
              max={maxRaiseToAmount}
              step="1"
              disabled={isLoading}
            />
          </div>

          {/* Slider */}
          <input
            type="range"
            className="raise-slider"
            min={minRaiseToAmount}
            max={maxRaiseToAmount}
            value={raiseAmount}
            onChange={handleRaiseAmountChange}
            disabled={isLoading}
          />

          <div className="amount-info">
            Min: ${minRaiseToAmount} | Max: ${maxRaiseToAmount} | Stack: ${playerStack}
          </div>
        </div>
      )}

      {isLoading && <p className="processing-message">Processing...</p>}
    </div>
  );
};

export default ActionControls;
