import React from 'react';
import './ChipStack.css';

interface ChipStackProps {
    amount: number;
    size?: 'small' | 'medium' | 'large';
    showAmount?: boolean;
}

// Calculate chip breakdown for realistic stack
const getChipBreakdown = (amount: number) => {
    const chips: { value: number; color: string; count: number }[] = [];
    let remaining = amount;

    const denominations = [
        { value: 1000, color: 'black' },
        { value: 500, color: 'purple' },
        { value: 100, color: 'blue' },
        { value: 25, color: 'green' },
        { value: 5, color: 'red' },
        { value: 1, color: 'white' },
    ];

    for (const denom of denominations) {
        const count = Math.floor(remaining / denom.value);
        if (count > 0) {
            chips.push({ ...denom, count: Math.min(count, 5) }); // Cap visual chips
            remaining %= denom.value;
        }
    }

    return chips.slice(0, 4); // Max 4 different denominations shown
};

const ChipStack: React.FC<ChipStackProps> = ({ amount, size = 'medium', showAmount = true }) => {
    if (amount <= 0) return null;

    const chips = getChipBreakdown(amount);
    const sizeClass = `chip-stack-${size}`;

    return (
        <div className={`chip-stack ${sizeClass}`}>
            <div className="chips-visual">
                {chips.map((chip, idx) => (
                    <div key={idx} className="chip-pile">
                        {Array.from({ length: Math.min(chip.count, 3) }).map((_, i) => (
                            <div
                                key={i}
                                className={`chip chip-${chip.color}`}
                                style={{
                                    transform: `translateY(${-i * 3}px)`,
                                    zIndex: i
                                }}
                            />
                        ))}
                    </div>
                ))}
            </div>
            {showAmount && <span className="chip-amount">${amount}</span>}
        </div>
    );
};

export default ChipStack;
