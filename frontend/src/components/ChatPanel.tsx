import React, { useRef, useEffect, useState } from 'react';
import './ChatPanel.css';

interface ChatMessage {
    id: number;
    sender: string;
    message: string;
    timestamp: Date;
    type: 'ai' | 'system' | 'action' | 'human';
}

interface ChatPanelProps {
    messages: ChatMessage[];
    onSendMessage?: (message: string) => void;
    gameId: string | null;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages, onSendMessage, gameId }) => {
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const [inputMessage, setInputMessage] = useState('');

    // Scroll to top when new messages arrive (newest first)
    useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = 0;
        }
    }, [messages]);

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const handleSendMessage = () => {
        if (inputMessage.trim() && onSendMessage && gameId) {
            onSendMessage(inputMessage.trim());
            setInputMessage('');
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Reverse messages so newest is on top
    const reversedMessages = [...messages].reverse();

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <span className="chat-icon">💬</span>
                <h3>Table Chat</h3>
            </div>
            <div className="chat-messages" ref={messagesContainerRef}>
                {messages.length === 0 ? (
                    <div className="chat-empty">
                        <p>Start a game to chat with the AIs...</p>
                    </div>
                ) : (
                    reversedMessages.map((msg) => (
                        <div key={msg.id} className={`chat-message ${msg.type}`}>
                            <div className="message-header">
                                <span className="message-sender">{msg.sender}</span>
                                <span className="message-time">{formatTime(msg.timestamp)}</span>
                            </div>
                            <div className="message-content">{msg.message}</div>
                        </div>
                    ))
                )}
            </div>
            {gameId && (
                <div className="chat-input-container">
                    <input
                        type="text"
                        className="chat-input"
                        placeholder="Trash talk the AIs... 🎯"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        maxLength={200}
                    />
                    <button
                        className="chat-send-btn"
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim()}
                    >
                        Send
                    </button>
                </div>
            )}
        </div>
    );
};

export default ChatPanel;
export type { ChatMessage };
