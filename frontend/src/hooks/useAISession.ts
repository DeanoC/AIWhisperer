import { useCallback, useEffect, useRef, useState } from 'react';
import { AIService } from '../services/aiService';
import { SessionInfo, SessionStatus, AIMessageChunk } from '../types/ai';

export function useAISession(aiService: AIService | undefined, userId: string) {
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [status, setStatus] = useState<SessionStatus>(SessionStatus.Idle);
  const [error, setError] = useState<string | null>(null);
  const [chunks, setChunks] = useState<AIMessageChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const aiServiceRef = useRef(aiService);


  useEffect(() => {
    aiServiceRef.current = aiService;
  }, [aiService]);

  // Listen for AI message chunks only if aiService is available
  useEffect(() => {
    if (!aiService) return;
    aiService.onAIMessageChunk((chunk) => {
      setChunks((prev) => [...prev, chunk]);
    });
  }, [aiService]);

  const startSession = useCallback(async () => {
    if (!aiServiceRef.current) return;
    setLoading(true);
    setError(null);
    setChunks([]);
    try {
      const info = await aiServiceRef.current.startSession(userId);
      setSessionInfo(info);
      setStatus(info.status);
    } catch (err: any) {
      setError(err.message || 'Failed to start session');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const stopSession = useCallback(async () => {
    if (!aiServiceRef.current) return;
    setLoading(true);
    setError(null);
    try {
      await aiServiceRef.current.stopSession();
      setStatus(SessionStatus.Stopped);
    } catch (err: any) {
      setError(err.message || 'Failed to stop session');
    } finally {
      setLoading(false);
    }
  }, []);

  const sendUserMessage = useCallback(async (message: string) => {
    if (!aiServiceRef.current) return;
    setLoading(true);
    setError(null);
    try {
      await aiServiceRef.current.sendUserMessage(message);
    } catch (err: any) {
      setError(err.message || 'Failed to send message');
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    sessionInfo,
    status,
    error,
    chunks,
    loading,
    startSession,
    stopSession,
    sendUserMessage,
  };
}
