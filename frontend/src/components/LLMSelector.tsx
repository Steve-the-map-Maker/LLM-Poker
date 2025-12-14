import React, { useState } from 'react';
import { PlayerConfig } from '../types/gameTypes';

interface LLMSelectorProps {
    onStartGame: (players: PlayerConfig[], blinds: number[]) => void;
    isLoading: boolean;
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ onStartGame, isLoading }) => {
    // Defines the AI type for each player seat
    const [playerTypes, setPlayerTypes] = useState<string[]>(["dummy", "dummy"]);
    const [geminiModels, setGeminiModels] = useState<string[]>(["gemini-2.5-flash-lite", "gemini-2.5-flash-lite"]); // Default model per player
    const [stackSize, setStackSize] = useState<number>(10000);
    const [bigBlind, setBigBlind] = useState<number>(100);

    const playerOptions = ["human", "dummy", "gemini"]; // GPT temporarily disabled
    const geminiModelOptions = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash"
    ];
    const gptModelOptions = [
        "gpt-3.5-turbo"
    ];
    const [gptModels, setGptModels] = useState<string[]>(["gpt-3.5-turbo", "gpt-3.5-turbo"]);

    const handleAddPlayer = () => {
        if (playerTypes.length < 6) {
            setPlayerTypes([...playerTypes, "dummy"]);
            setGeminiModels([...geminiModels, "gemini-2.5-flash-lite"]);
            setGptModels([...gptModels, "gpt-3.5-turbo"]);
        }
    };

    const handleRemovePlayer = (index: number) => {
        if (playerTypes.length > 2) {
            const newTypes = [...playerTypes];
            newTypes.splice(index, 1);
            setPlayerTypes(newTypes);

            const newModels = [...geminiModels];
            newModels.splice(index, 1);
            setGeminiModels(newModels);

            const newGptModels = [...gptModels];
            newGptModels.splice(index, 1);
            setGptModels(newGptModels);
        }
    };

    const handleTypeChange = (index: number, newType: string) => {
        const newTypes = [...playerTypes];
        newTypes[index] = newType;
        setPlayerTypes(newTypes);
    };

    const handleGeminiModelChange = (index: number, newModel: string) => {
        const newModels = [...geminiModels];
        newModels[index] = newModel;
        setGeminiModels(newModels);
    };

    const handleGptModelChange = (index: number, newModel: string) => {
        const newModels = [...gptModels];
        newModels[index] = newModel;
        setGptModels(newModels);
    };

    // Fun AI name generator
    const aiNames = {
        dummy: ["DumbBot", "RandomRick", "ChaosCarl", "LuckyLarry", "WildCard"],
        gemini: ["GeminiPro", "StarDust", "CosmicAce", "NebulaKing", "AstroBluffer"],
        gpt: ["GPT-Shark", "DeepThink", "TokenMaster", "PromptPro", "NeuralNate"],
        human: null // Humans name themselves
    };

    const getPlayerName = (type: string, index: number): string => {
        if (type === "human") return `You`;
        const names = aiNames[type as keyof typeof aiNames] || ["Bot"];
        if (!names) return `Player ${index + 1}`;
        // Pick a name based on index to keep it consistent
        return names[index % names.length];
    };

    const handleStart = () => {
        // Convert strings to PlayerConfig objects with the chosen stack
        const playersConfig: PlayerConfig[] = playerTypes.map((type, index) => ({
            name: getPlayerName(type, index),
            ai_type: type,
            stack: stackSize,
            gemini_model: type === 'gemini' ? geminiModels[index] : undefined,
            gpt_model: type === 'gpt' ? gptModels[index] : undefined
        }));

        const blinds = [Math.floor(bigBlind / 2), bigBlind];
        onStartGame(playersConfig, blinds);
    };

    return (
        <div className="selector-container">
            <h2>Game Setup</h2>

            {/* Global Settings */}
            <div className="game-settings" style={{ background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
                <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                        <label style={{ fontSize: '0.9em', marginBottom: '5px' }}>Starting Stack ($)</label>
                        <input
                            type="number"
                            value={stackSize}
                            onChange={(e) => setStackSize(parseInt(e.target.value) || 0)}
                            style={{ padding: '8px', width: '100px', borderRadius: '4px', border: '1px solid #444', background: '#222', color: 'white' }}
                        />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                        <label style={{ fontSize: '0.9em', marginBottom: '5px' }}>Big Blind ($)</label>
                        <input
                            type="number"
                            value={bigBlind}
                            onChange={(e) => setBigBlind(parseInt(e.target.value) || 0)}
                            style={{ padding: '8px', width: '100px', borderRadius: '4px', border: '1px solid #444', background: '#222', color: 'white' }}
                        />
                    </div>
                </div>
            </div>

            <h3>Players</h3>
            <div className="players-list" style={{ marginBottom: '20px' }}>
                {playerTypes.map((type, index) => (
                    <div key={index} className="player-row" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '10px 0', flexWrap: 'wrap', gap: '10px' }}>
                        <span style={{ marginRight: '10px', minWidth: '80px' }}>Player {index + 1}: </span>
                        <select
                            value={type}
                            onChange={(e) => handleTypeChange(index, e.target.value)}
                            disabled={isLoading}
                            style={{ padding: '5px', marginRight: '10px' }}
                        >
                            {playerOptions.map(opt => (
                                <option key={opt} value={opt}>
                                    {opt.charAt(0).toUpperCase() + opt.slice(1)}
                                </option>
                            ))}
                        </select>
                        {type === 'gemini' && (
                            <select
                                value={geminiModels[index]}
                                onChange={(e) => handleGeminiModelChange(index, e.target.value)}
                                disabled={isLoading}
                                style={{ padding: '5px', background: '#333', color: '#4CAF50', border: '1px solid #4CAF50', borderRadius: '4px' }}
                            >
                                {geminiModelOptions.map(model => (
                                    <option key={model} value={model}>
                                        {model}
                                    </option>
                                ))}
                            </select>
                        )}
                        {type === 'gpt' && (
                            <select
                                value={gptModels[index]}
                                onChange={(e) => handleGptModelChange(index, e.target.value)}
                                disabled={isLoading}
                                style={{ padding: '5px', background: '#333', color: '#2196F3', border: '1px solid #2196F3', borderRadius: '4px' }}
                            >
                                {gptModelOptions.map(model => (
                                    <option key={model} value={model}>
                                        {model}
                                    </option>
                                ))}
                            </select>
                        )}
                        {playerTypes.length > 2 && (
                            <button
                                onClick={() => handleRemovePlayer(index)}
                                disabled={isLoading}
                                style={{ background: '#ff4444', padding: '5px 10px', fontSize: '0.8em' }}
                            >
                                Remove
                            </button>
                        )}
                    </div>
                ))}
            </div>

            <div className="controls" style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                {playerTypes.length < 6 && (
                    <button onClick={handleAddPlayer} disabled={isLoading} style={{ background: '#2196F3' }}>
                        + Add Player
                    </button>
                )}
                <button onClick={handleStart} disabled={isLoading} style={{ background: '#4CAF50', fontWeight: 'bold' }}>
                    {isLoading ? 'Starting Game...' : 'Start Game'}
                </button>
            </div>

            <p style={{ fontSize: '0.9em', color: '#666', marginTop: '20px' }}>
                Note: "Human" players must control their actions manually.
            </p>
        </div>
    );
};

export default LLMSelector;
