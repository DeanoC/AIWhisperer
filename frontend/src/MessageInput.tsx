import React, { useRef, useState } from 'react';
import './MessageInput.css';

interface MessageInputProps {
  onSend: (text: string) => void;
  history: string[];
}

const MessageInput: React.FC<MessageInputProps> = ({ onSend, history }) => {
  const [input, setInput] = useState('');
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        onSend(input);
        setInput('');
        setHistoryIndex(null);
      }
    } else if (e.key === 'ArrowUp') {
      if (history.length > 0) {
        const idx = historyIndex === null ? history.length - 1 : Math.max(0, historyIndex - 1);
        setInput(history[idx]);
        setHistoryIndex(idx);
      }
    } else if (e.key === 'ArrowDown') {
      if (history.length > 0 && historyIndex !== null) {
        const idx = Math.min(history.length - 1, historyIndex + 1);
        setInput(history[idx]);
        setHistoryIndex(idx);
      }
    }
  };

  return (
    <div className="message-input-bar">
      <input
        ref={inputRef}
        className="message-input"
        type="text"
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter your message (Ctrl+Enter to send)"
        autoFocus
      />
      <button
        className="send-btn"
        onClick={() => {
          if (input.trim()) {
            onSend(input);
            setInput('');
            setHistoryIndex(null);
          }
        }}
      >
        Send
      </button>
    </div>
  );
};

export default MessageInput;
