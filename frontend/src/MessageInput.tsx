

import React, { useRef, useState, useEffect } from 'react';
import './MessageInput.css';

// Helper to parse command list from /help output
function parseCommandList(helpText: string): string[] {
  return helpText
    .split('\n')
    .map(line => line.trim())
    .filter(line => line.startsWith('/'))
    .map(line => line.split(':')[0].slice(1));
}


interface MessageInputProps {
  onSend: (text: string) => void;
  fetchCommandList: () => Promise<string[]>;
  sessionStatus?: any;
  disabled?: boolean;
  onFilePickerRequest?: (callback: (filePath: string) => void) => void;
}


const MessageInput: React.FC<MessageInputProps> = ({ onSend, fetchCommandList, sessionStatus, disabled, onFilePickerRequest }) => {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const [commandList, setCommandList] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [showingAtSymbol, setShowingAtSymbol] = useState(false);
  const [atSymbolPosition, setAtSymbolPosition] = useState(-1);

  // Fetch command list from backend (via fetchCommandList) on mount or when session becomes active
  useEffect(() => {
    if (commandList.length === 0 && fetchCommandList) {
      fetchCommandList().then(list => {
        setCommandList(list);
        // If user is already typing a command, show suggestions immediately
        if (input.startsWith('/') && list.length > 0) {
          setShowSuggestions(true);
        }
      }).catch(() => setCommandList([]));
    }
  }, [commandList.length, fetchCommandList, input, sessionStatus]);

  // Single source of truth for partial and filteredSuggestions
  const partial = input.startsWith('/') ? input.slice(1).split(' ')[0] : '';
  const filteredSuggestions: string[] = input.startsWith('/')
    ? commandList.filter(cmd => cmd.startsWith(partial))
    : [];

  useEffect(() => {
    if (input.startsWith('/') && filteredSuggestions.length > 0) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
    setSelectedIndex(0);
  }, [input, commandList.length, filteredSuggestions.length]);

  // Command detection: starts with slash or known command
  // For now, highlight the first word if it starts with '/'
  // Improved: always mirror the full input, only style the command part
  const getCommandHighlight = (text: string) => {
    if (!text.startsWith('/')) return { before: '', command: '', after: text, isCommand: false };
    const match = text.match(/^(\/\w+)(\b)?(.*)$/);
    if (match) {
      return {
        before: '',
        command: match[1],
        after: match[3] || '',
        isCommand: true,
      };
    }
    return { before: '', command: '', after: text, isCommand: false };
  };

  const { command, after, isCommand } = getCommandHighlight(input);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (showSuggestions && filteredSuggestions.length > 0) {
      if (e.key === 'ArrowDown' || e.key === 'Tab') {
        e.preventDefault();
        setSelectedIndex(i => (i + 1) % filteredSuggestions.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(i => (i - 1 + filteredSuggestions.length) % filteredSuggestions.length);
        return;
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredSuggestions[selectedIndex]) {
          const completed = '/' + filteredSuggestions[selectedIndex] + ' ';
          setInput(completed);
          setShowSuggestions(false);
          setSelectedIndex(0);
          setTimeout(() => {
            inputRef.current?.focus();
            // If the input is just a command (no args), send immediately
            if (completed.trim().split(' ').length === 1) {
              onSend(completed.trim());
              setInput('');
            }
          }, 0);
          return;
        }
      }
    }
    if (e.key === 'Escape') {
      setShowSuggestions(false);
      return;
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) {
        onSend(input);
        setInput('');
        setShowSuggestions(false);
        setSelectedIndex(0);
      }
    }
  };


  return (
    <div className="message-input-bar" style={{ position: 'relative' }}>
      {showSuggestions && filteredSuggestions.length > 0 && (
        <ul className="command-suggestions">
          {filteredSuggestions.map((cmd, i) => (
            <li
              key={cmd}
              className={i === selectedIndex ? 'selected' : ''}
              onMouseDown={e => {
                // Prevent input blur before click
                e.preventDefault();
                setInput('/' + cmd + ' ');
                setShowSuggestions(false);
                setSelectedIndex(0);
                setTimeout(() => inputRef.current?.focus(), 0);
              }}
            >
              /{cmd}
            </li>
          ))}
        </ul>
      )}
      <div className="input-highlight-wrapper">
        <div className="input-highlight">
          {isCommand
            ? <><span className="command-highlight">{command}</span><span className="after-command">{after || <span>&nbsp;</span>}</span></>
            : input || <span>&nbsp;</span>}
          {/* This div mirrors the input value for highlighting */}
        </div>
        <input
          ref={inputRef}
          className={`message-input${isCommand ? ' command-mode' : ''}`}
          type="text"
          value={input}
          onChange={e => {
            const newValue = e.target.value;
            const oldValue = input;
            
            // Check if @ was just typed
            if (newValue.length > oldValue.length) {
              const lastChar = newValue[newValue.length - 1];
              if (lastChar === '@' && onFilePickerRequest) {
                // Check if @ is at word boundary (start of input or after space)
                const prevChar = newValue[newValue.length - 2];
                if (!prevChar || prevChar === ' ') {
                  setShowingAtSymbol(true);
                  setAtSymbolPosition(newValue.length - 1);
                  
                  // Request file picker
                  onFilePickerRequest((filePath: string) => {
                    // Replace @ with the file path
                    const beforeAt = newValue.substring(0, atSymbolPosition);
                    const afterAt = newValue.substring(atSymbolPosition + 1);
                    const newInput = beforeAt + filePath + afterAt;
                    setInput(newInput);
                    setShowingAtSymbol(false);
                    setAtSymbolPosition(-1);
                    
                    // Focus back on input
                    setTimeout(() => inputRef.current?.focus(), 0);
                  });
                }
              }
            }
            
            setInput(newValue);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Enter your message and press Enter to send"
          autoFocus
          disabled={disabled}
        />
      </div>
      <button
        className="send-btn"
        onClick={() => {
          if (input.trim()) {
            onSend(input);
            setInput('');
          }
        }}
        disabled={disabled}
      >
        Send
      </button>
    </div>
  );
};

export default MessageInput;
