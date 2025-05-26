
import React, { useState } from 'react';
import './App.css';
import ModelList from './ModelList';
import ChatWindow, { ChatMessage } from './ChatWindow';
import MessageInput from './MessageInput';

const initialMessages: ChatMessage[] = [
  {
    sender: 'user',
    text: 'Qwen: Qwen3 4B (free) (qwen/qwen3-4b:free)\nQwen3-4B is a 4 billion parameter dense language model from the Qwen3 series, designed to support both general-purpose and reasoning-intensive tasks. It introduces a dual-mode architecture—thinking and non-thinking—allowing dynamic switching between high-precision logical reasoning and efficient dialogue generation. This makes it well-suited for multi-turn chat, instruction following, and complex agent workflows.\n\nAsking AI about qwen/qwen3-4b:free...'
  },
  {
    sender: 'ai',
    text: "I'm sorry for any confusion, but as of my current knowledge base, there doesn't seem to be a specific AI model named 'qwen/qwen3-4b:free' supported by OpenRouter. OpenAI has developed many models like GPT-3, DAVINCI, etc.\n\nHowever, the name you've provided doesn't match any known models. It's possible that there might be a typo or misunderstanding in the name you've given. If you have more details or if there's a specific aspect of AI you're interested in, feel free to ask!"
  }
];

function App() {
  const [selectedModel, setSelectedModel] = useState('qwen/qwen3-4b:free');
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [history, setHistory] = useState<string[]>([]);

  const handleSend = (text: string) => {
    setMessages([...messages, { sender: 'user', text }]);
    setHistory([...history, text]);
    // Simulate AI response (replace with backend call)
    setTimeout(() => {
      setMessages(msgs => [
        ...msgs,
        { sender: 'ai', text: `AI response to: ${text}` }
      ]);
    }, 500);
  };

  return (
    <div className="main-layout">
      <div className="sidebar">
        <ModelList selected={selectedModel} onSelect={setSelectedModel} />
      </div>
      <div className="content-area">
        <ChatWindow messages={messages} />
        <MessageInput onSend={handleSend} history={history} />
      </div>
    </div>
  );
}

export default App;
