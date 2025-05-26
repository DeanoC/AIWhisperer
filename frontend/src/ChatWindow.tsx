import React from 'react';
import './ChatWindow.css';

export interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
}

interface ChatWindowProps {
  messages: ChatMessage[];
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages }) => (
  <div className="chat-window">
    {messages.map((msg, idx) => (
      <div
        key={idx}
        className={`chat-message ${msg.sender === 'user' ? 'user' : 'ai'}`}
      >
        {msg.text}
      </div>
    ))}
  </div>
);

export default ChatWindow;
