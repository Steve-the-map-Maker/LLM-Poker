import React, { useState } from 'react';
import { PlayerConfig } from '../types/gameTypes';
import './LLMSelector.css';

interface LLMSelectorProps {
    onStartGame: (players: PlayerConfig[], blinds: number[]) => void;
    isLoading: boolean;
}

const LLMSelector: React.FC<LLMSelectorProps> = ({ onStartGame, isLoading }) => {
    // Defines the AI type for each player seat
    const [playerTypes, setPlayerTypes] = useState<string[]>(["human", "gemini"]);
    const [geminiModels, setGeminiModels] = useState<string[]>(["gemini-3.1-flash-lite-preview", "gemini-3.1-flash-lite-preview"]); // Default: Gemini 3.1 Flash Lite
    const [claudeModels, setClaudeModels] = useState<string[]>(["claude-3-haiku-20240307", "claude-3-haiku-20240307"]); // Default: Claude 3 Haiku
    const [stackSize, setStackSize] = useState<number>(10000);
    const [bigBlind, setBigBlind] = useState<number>(100);

    const playerOptions = ["human", "gemini", "claude"];
    const geminiModelOptions = [
        "gemini-3.1-flash-lite-preview"
    ];
    const claudeModelOptions = [
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-latest",
        "claude-3-opus-20240229"
    ];

    // Custom AI prompts for each player
    const DEFAULT_AI_PROMPT = `Style: Aggressive and confident\nTrash talk: Taunt opponents when you bluff successfully\nStrategy: Mix up your play, occasionally slow-play strong hands`;
    const [customPrompts, setCustomPrompts] = useState<string[]>([DEFAULT_AI_PROMPT, DEFAULT_AI_PROMPT]);
    const [showAdvanced, setShowAdvanced] = useState<boolean[]>([false, false]);

    const handleAddPlayer = () => {
        if (playerTypes.length < 6) {
            setPlayerTypes([...playerTypes, "gemini"]);
            setGeminiModels([...geminiModels, "gemini-3.1-flash-lite-preview"]);
            setClaudeModels([...claudeModels, "claude-3-haiku-20240307"]);
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

            const newClaudeModels = [...claudeModels];
            newClaudeModels.splice(index, 1);
            setClaudeModels(newClaudeModels);

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

    const handleClaudeModelChange = (index: number, newModel: string) => {
        const newModels = [...claudeModels];
        newModels[index] = newModel;
        setClaudeModels(newModels);
    };

    const aiNames = {
        gemini: ["GeminiPro", "StarDust", "CosmicAce", "NebulaKing", "AstroBluffer"],
        claude: ["Claude", "AnthropicAce", "HaikuHustler", "SonnetShark", "OpusOne"],
        human: null
    };

    const getPlayerName = (type: string, index: number): string => {
        if (type === "human") return `You`;
        const names = aiNames[type as keyof typeof aiNames] || ["Bot"];
        if (!names) return `Player ${index + 1}`;
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
        const playersConfig: PlayerConfig[] = playerTypes.map((type, index) => ({
            name: getPlayerName(type, index),
            ai_type: type,
            stack: stackSize,
            gemini_model: type === 'gemini' ? geminiModels[index] : undefined,
            claude_model: type === 'claude' ? claudeModels[index] : undefined,
            custom_prompt: (type === 'gemini' || type === 'claude') ? customPrompts[index] : undefined
        }));

        const blinds = [Math.floor(bigBlind / 2), bigBlind];
        onStartGame(playersConfig, blinds);
    };

    const getTypeIcon = (type: string) => {
        if (type === "human") return "🧑‍💻";
        if (type === "gemini") return "🤖";
        if (type === "claude") return "🧠";
        return "👤";
    };

    return (
        <div className="selector-wrapper">
            <div className="selector-container">
                <h2>LLM Poker Setup</h2>

                {/* Global Settings */}
                <div className="game-settings-card">
                    <div className="setting-group">
                        <label>Starting Stack ($)</label>
                        <input
                            className="premium-input"
                            type="number"
                            value={stackSize}
                            onChange={(e) => setStackSize(parseInt(e.target.value) || 0)}
                        />
                    </div>
                    <div className="setting-group">
                        <label>Big Blind ($)</label>
                        <input
                            className="premium-input"
                            type="number"
                            value={bigBlind}
                            onChange={(e) => setBigBlind(parseInt(e.target.value) || 0)}
                        />
                    </div>
                </div>

                <h3>Table Setup</h3>
                <div className="players-list">
                    {playerTypes.map((type, index) => (
                        <div key={index} className={`player-card ${type}-border`}>
                            <span className="player-label">
                                {getTypeIcon(type)} P{index + 1}
                            </span>
                            
                            <select
                                className="premium-select"
                                value={type}
                                onChange={(e) => handleTypeChange(index, e.target.value)}
                                disabled={isLoading}
                            >
                                {playerOptions.map(opt => (
                                    <option key={opt} value={opt} disabled={opt === 'claude'}>
                                        {opt.charAt(0).toUpperCase() + opt.slice(1)} {opt === 'claude' ? '(Disabled)' : ''}
                                    </option>
                                ))}
                            </select>

                            {type === 'gemini' && (
                                <select
                                    className="premium-select gemini-variant"
                                    value={geminiModels[index]}
                                    onChange={(e) => handleGeminiModelChange(index, e.target.value)}
                                    disabled={isLoading}
                                >
                                    {geminiModelOptions.map(model => (
                                        <option key={model} value={model}>
                                            {model}
                                        </option>
                                    ))}
                                </select>
                            )}

                            {type === 'claude' && (
                                <select
                                    className="premium-select claude-variant"
                                    value={claudeModels[index]}
                                    onChange={(e) => handleClaudeModelChange(index, e.target.value)}
                                    disabled={isLoading}
                                >
                                    {claudeModelOptions.map(model => (
                                        <option key={model} value={model}>
                                            {model}
                                        </option>
                                    ))}
                                </select>
                            )}

                            {(type === 'gemini' || type === 'claude') && (
                                <button
                                    className={`btn btn-toggle ${showAdvanced[index] ? 'active' : ''}`}
                                    onClick={() => toggleAdvanced(index)}
                                    disabled={isLoading}
                                >
                                    {showAdvanced[index] ? '▲ Hide Settings' : '⚙️ Custom AI'}
                                </button>
                            )}

                            {playerTypes.length > 2 && (
                                <button
                                    className="btn btn-remove"
                                    onClick={() => handleRemovePlayer(index)}
                                    disabled={isLoading}
                                >
                                    ✕
                                </button>
                            )}

                            {/* Dropdown area for advanced custom settings */}
                            {showAdvanced[index] && (type === 'gemini' || type === 'claude') && (
                                <div className="advanced-area">
                                    <label>AI Personality & Strategy Setup</label>
                                    <textarea
                                        className="advanced-textarea"
                                        value={customPrompts[index]}
                                        onChange={(e) => handleCustomPromptChange(index, e.target.value)}
                                        disabled={isLoading}
                                        maxLength={500}
                                        rows={4}
                                        placeholder="Describe the AI's personality, playing style, and trash talk..."
                                    />
                                    <span className="char-counter">
                                        {customPrompts[index].length} / 500 characters
                                    </span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                <div className="controls">
                    {playerTypes.length < 6 && (
                        <button className="btn btn-add" onClick={handleAddPlayer} disabled={isLoading}>
                            + Add Player
                        </button>
                    )}
                    <button className="btn btn-start" onClick={handleStart} disabled={isLoading}>
                        {isLoading ? 'Starting...' : '♦ Start Game ♠'}
                    </button>
                </div>

                <p className="note-text">
                    Note: "Human" players must control their actions manually.
                </p>
            </div>
        </div>
    );
};

export default LLMSelector;
