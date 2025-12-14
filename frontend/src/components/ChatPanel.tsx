import React, { useRef, useEffect } from 'react';
import './ChatPanel.css';

interface ChatMessage {
    id: number;
    sender: string;
    message: string;
    timestamp: Date;
    type: 'ai' | 'system' | 'action';
}

interface ChatPanelProps {
    messages: ChatMessage[];
}

const ChatPanel: React.FC<ChatPanelProps> = ({ messages }) => {
    const messagesContainerRef = useRef<HTMLDivElement>(null);

    // Scroll to top when new messages arrive (newest first)
    useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = 0;
        }
    }, [messages]);

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Reverse messages so newest is on top
    const reversedMessages = [...messages].reverse();

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <span className="chat-icon">🤖</span>
                <h3>AI Thoughts</h3>
            </div>
            <div className="chat-messages" ref={messagesContainerRef}>
                {messages.length === 0 ? (
                    <div className="chat-empty">
                        <p>Start a game to see AI thinking...</p>
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
        </div>
    );
};

export default ChatPanel;
export type { ChatMessage };
