import React, { useState } from 'react';
import { PlayerConfig } from '../types/gameTypes';

interface LLMSelectorProps {
    onStartGame: (players: PlayerConfig[], blinds: number[]) => void;
    isLoading: boolean;
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ onStartGame, isLoading }) => {
    // Defines the AI type for each player seat
    const [playerTypes, setPlayerTypes] = useState<string[]>(["human", "gemini"]);
    const [geminiModels, setGeminiModels] = useState<string[]>(["gemini-3-flash-preview", "gemini-3-flash-preview"]); // Default: Gemini 3 Flash Preview
    const [stackSize, setStackSize] = useState<number>(10000);
    const [bigBlind, setBigBlind] = useState<number>(100);

    const playerOptions = ["human", "gemini"];
    const geminiModelOptions = [
        // Gemini 3 Flash (Newest!)
        "gemini-3-flash-preview",
        // Gemini 2.5 Flash
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        // Gemini 2.0 Flash
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        // Gemini 1.5 Flash
        "gemini-1.5-flash"
    ];

    // Custom AI prompts for each player
    const DEFAULT_AI_PROMPT = `Style: Aggressive and confident
Trash talk: Taunt opponents when you bluff successfully
Strategy: Mix up your play, occasionally slow-play strong hands`;
    const [customPrompts, setCustomPrompts] = useState<string[]>([DEFAULT_AI_PROMPT, DEFAULT_AI_PROMPT]);
    const [showAdvanced, setShowAdvanced] = useState<boolean[]>([false, false]);

    const handleAddPlayer = () => {
        if (playerTypes.length < 6) {
            setPlayerTypes([...playerTypes, "gemini"]);
            setGeminiModels([...geminiModels, "gemini-3-flash-preview"]);
            setCustomPrompts([...customPrompts, DEFAULT_AI_PROMPT]);
            setShowAdvanced([...showAdvanced, false]);
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

            const newPrompts = [...customPrompts];
            newPrompts.splice(index, 1);
            setCustomPrompts(newPrompts);

            const newShowAdvanced = [...showAdvanced];
            newShowAdvanced.splice(index, 1);
            setShowAdvanced(newShowAdvanced);
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

    // Fun AI name generator
    const aiNames = {
        gemini: ["GeminiPro", "StarDust", "CosmicAce", "NebulaKing", "AstroBluffer"],
        human: null // Humans name themselves
    };

    const getPlayerName = (type: string, index: number): string => {
        if (type === "human") return `You`;
        const names = aiNames[type as keyof typeof aiNames] || ["Bot"];
        if (!names) return `Player ${index + 1}`;
        // Pick a name based on index to keep it consistent
        return names[index % names.length];
    };

    const handleCustomPromptChange = (index: number, newPrompt: string) => {
        const newPrompts = [...customPrompts];
        newPrompts[index] = newPrompt;
        setCustomPrompts(newPrompts);
    };

    const toggleAdvanced = (index: number) => {
        const newShowAdvanced = [...showAdvanced];
        newShowAdvanced[index] = !newShowAdvanced[index];
        setShowAdvanced(newShowAdvanced);
    };

    const handleStart = () => {
        // Convert strings to PlayerConfig objects with the chosen stack
        const playersConfig: PlayerConfig[] = playerTypes.map((type, index) => ({
            name: getPlayerName(type, index),
            ai_type: type,
            stack: stackSize,
            gemini_model: type === 'gemini' ? geminiModels[index] : undefined,
            custom_prompt: type === 'gemini' ? customPrompts[index] : undefined
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
                        {playerTypes.length > 2 && (
                            <button
                                onClick={() => handleRemovePlayer(index)}
                                disabled={isLoading}
                                style={{ background: '#ff4444', padding: '5px 10px', fontSize: '0.8em' }}
                            >
                                Remove
                            </button>
                        )}
                        {type === 'gemini' && (
                            <button
                                onClick={() => toggleAdvanced(index)}
                                style={{
                                    background: showAdvanced[index] ? '#666' : '#555',
                                    padding: '5px 10px',
                                    fontSize: '0.8em',
                                    border: '1px solid #777'
                                }}
                            >
                                {showAdvanced[index] ? '▲ Hide' : '⚙️ Customize AI'}
                            </button>
                        )}
                        {showAdvanced[index] && type === 'gemini' && (
                            <div style={{
                                width: '100%',
                                marginTop: '10px',
                                padding: '10px',
                                background: 'rgba(255,255,255,0.05)',
                                borderRadius: '8px',
                                border: '1px solid #444'
                            }}>
                                <label style={{ fontSize: '0.85em', display: 'block', marginBottom: '5px', color: '#aaa' }}>
                                    AI Personality & Strategy:
                                </label>
                                <textarea
                                    value={customPrompts[index]}
                                    onChange={(e) => handleCustomPromptChange(index, e.target.value)}
                                    disabled={isLoading}
                                    maxLength={500}
                                    rows={4}
                                    style={{
                                        width: '100%',
                                        padding: '8px',
                                        borderRadius: '4px',
                                        border: '1px solid #555',
                                        background: '#222',
                                        color: '#ddd',
                                        fontSize: '0.9em',
                                        resize: 'vertical',
                                        boxSizing: 'border-box'
                                    }}
                                    placeholder="Describe the AI's personality, playing style, and trash talk..."
                                />
                                <span style={{ fontSize: '0.75em', color: '#666' }}>
                                    {customPrompts[index].length}/500 characters
                                </span>
                            </div>
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
