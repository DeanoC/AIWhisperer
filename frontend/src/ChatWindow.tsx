import React from 'react';
import './ChatWindow.css';
import { ChatMessage, MessageSender } from './types/chat';

interface ChatWindowProps {
  messages: ChatMessage[];
}

const ChatWindow: React.FC<ChatWindowProps> = ({ messages }) => (
  <div className="chat-window">
    {messages.map((msg, idx) => (
      <div
        key={msg.id || idx}
        className={`chat-message ${msg.sender === MessageSender.User ? 'user' : msg.sender === MessageSender.AI ? 'ai' : 'system'}`}
      >
        {msg.content}
      </div>
    ))}
  </div>
);

export default ChatWindow;
