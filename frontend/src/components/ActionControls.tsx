import React, { useState, useEffect } from 'react';

interface ActionControlsProps {
  gameId: string | null;
  humanPlayerIndex: number | null;
  isHumanTurn: boolean;
  availableActions: string[]; // e.g., ["fold", "check_or_call", "complete_bet_or_raise_to"]
  checkingOrCallingAmount: number;
  minRaiseToAmount: number;
  maxRaiseToAmount: number; // This would typically be the player's stack + what they've already put in
  playerStack: number; // The human player's current stack (remaining chips)
  onPlayerAction: (actionType: string, amount?: number) => void; // Callback to App.tsx
  isLoading: boolean; // To disable controls during API calls
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
}) => {
  const [raiseAmount, setRaiseAmount] = useState<number>(minRaiseToAmount);

  useEffect(() => {
    // Reset raise amount when minRaiseToAmount changes (e.g. new betting round or opponent action)
    setRaiseAmount(minRaiseToAmount > 0 ? minRaiseToAmount : 0);
  }, [minRaiseToAmount]);

  if (!isHumanTurn || !gameId || humanPlayerIndex === null || availableActions.length === 0) {
    return null; // Don't render if not human's turn or no actions available
  }

  const canFold = availableActions.includes('fold');
  // Correctly determine if Check or Call is possible based on 'check_or_call' and checkingOrCallingAmount
  const isCheckOrCallAvailable = availableActions.includes('check_or_call');
  const canCheck = isCheckOrCallAvailable && checkingOrCallingAmount === 0;
  const canCall = isCheckOrCallAvailable && checkingOrCallingAmount > 0;

  const canBet = availableActions.includes('bet') || (availableActions.includes('complete_bet_or_raise_to') && checkingOrCallingAmount === 0); // Bet if no call amount
  const canRaise = availableActions.includes('raise') || (availableActions.includes('complete_bet_or_raise_to') && checkingOrCallingAmount > 0); // Raise if there is a call amount

  const handleFold = () => onPlayerAction('fold');
  const handleCheck = () => onPlayerAction('check'); // Action type for backend is 'check'
  const handleCall = () => onPlayerAction('call'); // Action type for backend is 'call'
  const handleBet = () => {
    if (raiseAmount >= minRaiseToAmount && raiseAmount <= maxRaiseToAmount) {
      onPlayerAction('bet', raiseAmount);
    } else {
      alert(`Bet amount must be between ${minRaiseToAmount} and ${maxRaiseToAmount}. Your stack: ${playerStack}`);
    }
  };
  const handleRaise = () => {
    if (raiseAmount >= minRaiseToAmount && raiseAmount <= maxRaiseToAmount) {
      onPlayerAction('raise', raiseAmount);
    } else {
      alert(`Raise amount must be between ${minRaiseToAmount} and ${maxRaiseToAmount}. Your stack: ${playerStack}`);
    }
  };

  const handleRaiseAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    setRaiseAmount(isNaN(value) ? 0 : value);
  };

  return (
    <div className="action-controls">
      <h4>Your Turn (Player {humanPlayerIndex})</h4>
      <div>
        {canFold && <button onClick={handleFold} disabled={isLoading}>Fold</button>}
        {/* Display Check or Call button based on the derived booleans */}
        {canCheck && <button onClick={handleCheck} disabled={isLoading}>Check</button>}
        {canCall && <button onClick={handleCall} disabled={isLoading}>Call {checkingOrCallingAmount}</button>}
      </div>
      {(canBet || canRaise) && (
        <div style={{ marginTop: '10px' }}>
          <label htmlFor="raiseAmount">Amount:</label>
          <input
            type="number"
            id="raiseAmount"
            value={raiseAmount}
            onChange={handleRaiseAmountChange}
            min={minRaiseToAmount}
            max={maxRaiseToAmount} // Player's effective stack
            step="1" // Assuming integer bets
            disabled={isLoading}
          />
          {canBet && <button onClick={handleBet} disabled={isLoading || raiseAmount < minRaiseToAmount || raiseAmount > maxRaiseToAmount}>Bet</button>}
          {canRaise && <button onClick={handleRaise} disabled={isLoading || raiseAmount < minRaiseToAmount || raiseAmount > maxRaiseToAmount}>Raise to {raiseAmount}</button>}
          <button
            onClick={() => onPlayerAction(canBet ? 'bet' : 'raise', maxRaiseToAmount)}
            disabled={isLoading}
            style={{ backgroundColor: '#dc3545', marginLeft: '5px' }}
          >
            🔥 All-In ({maxRaiseToAmount})
          </button>
          <input
            type="range"
            min={minRaiseToAmount}
            max={maxRaiseToAmount}
            value={raiseAmount}
            onChange={handleRaiseAmountChange}
            disabled={isLoading}
            style={{ width: "100px", marginLeft: "10px" }}
          />
          <small> (Min: {minRaiseToAmount}, Max: {maxRaiseToAmount}, Stack: {playerStack})</small>
        </div>
      )}
      {isLoading && <p>Processing action...</p>}
    </div>
  );
};

export default ActionControls;
