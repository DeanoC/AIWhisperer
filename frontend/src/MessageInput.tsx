import React, { useRef, useState } from 'react';
import './MessageInput.css';


interface MessageInputProps {
  onSend: (text: string) => void;
}


const MessageInput: React.FC<MessageInputProps> = ({ onSend }) => {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        onSend(input);
        setInput('');
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
        placeholder="Enter your message and press Enter to send"
        autoFocus
      />
      <button
        className="send-btn"
        onClick={() => {
          if (input.trim()) {
            onSend(input);
            setInput('');
            //
          }
        }}
      >
        Send
      </button>
    </div>
  );
};

export default MessageInput;
