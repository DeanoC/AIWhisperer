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
        {msg.sender === MessageSender.System && msg.content.startsWith('ERROR:') ? (
          <span className="system-error">{msg.content.split('\n').map((line, i) => (
            <React.Fragment key={i}>
              {line}
              {i < msg.content.split('\n').length - 1 && <br />}
            </React.Fragment>
          ))}</span>
        ) : (
          msg.content.split('\n').map((line, i) => (
            <React.Fragment key={i}>
              {line}
              {i < msg.content.split('\n').length - 1 && <br />}
            </React.Fragment>
          ))
        )}
      </div>
    ))}
  </div>
);

export default ChatWindow;
