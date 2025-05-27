

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
import { SessionStatus } from './types/ai';
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
    if (ws && wsStatus === 'connected') {
      console.log('[App] WebSocket is connected, initializing AIService');
      const jsonRpc = new JsonRpcService(ws);
      setAIService(new AIService(jsonRpc));
    } else {
      setAIService(undefined);
    }
  }, [ws, wsStatus]);

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
    console.log('[handleSend] called with:', text);
    if (!aiService || !sessionHooks) {
      console.warn('[handleSend] No aiService or sessionHooks');
      // Optionally, add a system message to the chat
      // addSystemMessage && addSystemMessage('Backend not connected. Please check your server.');
      return;
    }
    addUserMessage(text);
    // Start session if needed
    // Map numeric status to string using SessionStatus enum if needed
    let isActive = false;
    if (typeof sessionStatus === 'string') {
      isActive = sessionStatus === SessionStatus.Active;
    } else if (typeof sessionStatus === 'number') {
      // Backend sends 1 for active, 0 for idle, 2 for stopped, etc.
      // Map to SessionStatus enum
      isActive = sessionStatus === 1;
    }
    if (!sessionInfo || !isActive) {
      console.log('[handleSend] Starting session...');
      await startSession?.();
      // Wait for session to become active
      let tries = 0;
      let currentStatus = sessionHooks.status;
      while (tries < 10) {
        await new Promise(res => setTimeout(res, 100));
        let polledStatus = aiService?.getStatus ? aiService.getStatus() : undefined;
        let isCurrentActive = false;
        if (typeof polledStatus === 'string') {
          isCurrentActive = polledStatus === SessionStatus.Active;
        } else if (typeof polledStatus === 'number') {
          isCurrentActive = polledStatus === 1;
        }
        console.log(`[handleSend] Waiting for session to become active... status: ${polledStatus}`);
        if (isCurrentActive) break;
        tries++;
      }
      let finalStatus = aiService?.getStatus ? aiService.getStatus() : undefined;
      console.log('[handleSend] Session status after start:', finalStatus);
    }
    // Final check
    // Use the latest status from aiService for the final check
    let latestStatus = aiService?.getStatus ? aiService.getStatus() : undefined;
    let isFinalActive = false;
    if (typeof latestStatus === 'string') {
      isFinalActive = latestStatus === SessionStatus.Active;
    } else if (typeof latestStatus === 'number') {
      isFinalActive = latestStatus === 1;
    }
    console.log('[handleSend] Final status check:', latestStatus, typeof latestStatus, 'isFinalActive:', isFinalActive);
    if (!isFinalActive) {
      console.error('[handleSend] Session is not active, aborting send.');
      return;
    }
    // Only abort if not active; otherwise, continue to send the message
    startAIMessage();
    console.log('[handleSend] Sending user message:', text);
    await sendUserMessage?.(text);
    console.log('[handleSend] sendUserMessage complete');
  };

  // Set AI message chunk handler ONCE when aiService changes
  // Ensure only one AI chunk handler is set, and clean up on unmount or aiService change
  useEffect(() => {
    if (!aiService) return;
    aiService.onAIMessageChunk(appendAIChunk);
    return () => {
      // Remove the handler when aiService changes or component unmounts
      aiService.onAIMessageChunk(() => {});
    };
  }, [aiService, appendAIChunk]);

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
