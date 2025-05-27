

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
  // Start a session as soon as AIService and startSession are available, and session is not active
  useEffect(() => {
    if (
      aiService &&
      typeof startSession === 'function' &&
      sessionStatus !== SessionStatus.Active
    ) {
      startSession();
    }
    // Only run when aiService, sessionStatus, or startSession changes
  }, [aiService, sessionStatus, startSession]);
  const {
    messages,
    // loading: chatLoading,
    addUserMessage,
    startAIMessage,
    appendAIChunk,
    addSystemMessage,
  } = useChat();

  // Send user message handler
  // Ensure session is started before sending a message
  const handleSend = async (text: string) => {
    console.log('[handleSend] called with:', text);
    if (!aiService || !sessionHooks) {
      console.warn('[handleSend] No aiService or sessionHooks');
      return;
    }
    addUserMessage(text);
    // Start session if needed
    let isActive = false;
    if (typeof sessionStatus === 'string') {
      isActive = sessionStatus === SessionStatus.Active;
    } else if (typeof sessionStatus === 'number') {
      isActive = sessionStatus === 1;
    }
    if (!sessionInfo || !isActive) {
      console.log('[handleSend] Starting session...');
      await startSession?.();
      let tries = 0;
      while (tries < 10) {
        await new Promise(res => setTimeout(res, 100));
        let polledStatus = aiService?.getStatus ? aiService.getStatus() : undefined;
        let isCurrentActive = false;
        if (typeof polledStatus === 'string') {
          isCurrentActive = polledStatus === SessionStatus.Active;
        } else if (typeof polledStatus === 'number') {
          isCurrentActive = polledStatus === 1;
        }
        if (isCurrentActive) break;
        tries++;
      }
    }
    let latestStatus = aiService?.getStatus ? aiService.getStatus() : undefined;
    let isFinalActive = false;
    if (typeof latestStatus === 'string') {
      isFinalActive = latestStatus === SessionStatus.Active;
    } else if (typeof latestStatus === 'number') {
      isFinalActive = latestStatus === 1;
    }
    if (!isFinalActive) {
      return;
    }
    // Command detection: if input starts with '/', treat as command
    if (text.trim().startsWith('/')) {
      try {
        startAIMessage();
        const result = await aiService.dispatchCommand(text.trim());
        // Display command output in chat (as system/AI message)
        // If the command is a system/command result, show as system message
        if (result.error) {
          addSystemMessage('ERROR: ' + result.error);
        } else {
          addSystemMessage(result.output || JSON.stringify(result));
        }
      } catch (err: any) {
        appendAIChunk({ content: `Command error: ${err.message || err}`, index: 0, isFinal: true });
      }
    } else {
      startAIMessage();
      await sendUserMessage?.(text);
    }
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

  // Fetch command list for tab completion (calls /help and parses output)
  function fetchCommandList(): Promise<string[]> {
    if (!aiService) return Promise.resolve([]);
    return aiService.dispatchCommand('/help').then(result => {
      const helpText = typeof result === 'string' ? result : (result?.output || '');
      return helpText
        .split('\n')
        .map((line: any) => (typeof line === 'string' ? line.trim() : ''))
        .filter((line: any) => typeof line === 'string' && line.startsWith('/'))
        .map((line: any) => (typeof line === 'string' ? line.split(':')[0].slice(1) : ''));
    }).catch(() => []);
  }

  return (
    <div className="main-layout">
      <div className="sidebar">
      </div>
      <div className="content-area">
        <div className="status-bar">
          WebSocket: {wsStatus}
          {sessionStatus && <> | Session: {sessionStatus}</>}
          {sessionError && <span className="error">Error: {sessionError}</span>}
        </div>
        <ChatWindow messages={messages} />
        <MessageInput onSend={handleSend} fetchCommandList={fetchCommandList} sessionStatus={sessionStatus} />

      </div>
    </div>
  );
}

export default App;
