

import React, { useState, useEffect } from 'react';
import './App.css';
import ModelList from './ModelList';
import ChatWindow from './ChatWindow';
import MessageInput from './MessageInput';

import { useWebSocket } from './hooks/useWebSocket';
import { AIService } from './services/aiService';
import { JsonRpcService } from './services/jsonRpcService';
import { useAISession } from './hooks/useAISession';
import { useChat } from './hooks/useChat';
// import { MessageSender } from './types/chat';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
const USER_ID = 'demo-user';

function App() {
  const [selectedModel, setSelectedModel] = useState('qwen/qwen3-4b:free');

  // WebSocket connection

  const { status: wsStatus, ws } = useWebSocket(WS_URL);

  // AIService instance (memoized)
  const [aiService, setAIService] = useState<AIService | undefined>(undefined);

  // Only initialize AIService when WebSocket is truly open
  useEffect(() => {
    if (ws) {
      const jsonRpc = new JsonRpcService(ws);
      setAIService(new AIService(jsonRpc));
    } else {
      setAIService(undefined);
    }
  }, [ws]);

  // AI session management
  const sessionHooks = useAISession(aiService, USER_ID);
  const sessionInfo = sessionHooks.sessionInfo;
  const sessionStatus = sessionHooks.status;
  const sessionError = sessionHooks.error;
  const startSession = sessionHooks.startSession;
  const sendUserMessage = sessionHooks.sendUserMessage;

  // Chat state management
  const {
    messages,
    // loading: chatLoading,
    addUserMessage,
    startAIMessage,
    appendAIChunk,
    // addSystemMessage,
  } = useChat();

  // Send user message handler
  // Ensure session is started before sending a message
  const handleSend = async (text: string) => {
    if (!aiService || !sessionHooks) {
      // Optionally, add a system message to the chat
      // addSystemMessage && addSystemMessage('Backend not connected. Please check your server.');
      return;
    }
    addUserMessage(text);
    // Start session if needed
    if (!sessionInfo || sessionStatus !== 'active') {
      console.log('Starting session...');
      await startSession?.();
      // Wait for session to become active
      let tries = 0;
      while (sessionStatus !== 'active' && tries < 10) {
        await new Promise(res => setTimeout(res, 100));
        tries++;
      }
      console.log('Session status after start:', sessionStatus);
    }
    startAIMessage();
    aiService.onAIMessageChunk(appendAIChunk);
    console.log('Sending user message:', text);
    await sendUserMessage?.(text);
    // (Chunks will be appended as they arrive)
  };

  return (
    <div className="main-layout">
      <div className="sidebar">
        <ModelList selected={selectedModel} onSelect={setSelectedModel} />
      </div>
      <div className="content-area">
        <div className="status-bar">
          WebSocket: {wsStatus}
          {sessionStatus && <> | Session: {sessionStatus}</>}
          {sessionError && <span className="error">Error: {sessionError}</span>}
        </div>
        <ChatWindow messages={messages} />
        <MessageInput onSend={handleSend} />
      </div>
    </div>
  );
}

export default App;
