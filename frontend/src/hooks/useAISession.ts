
import { useCallback, useEffect, useRef, useState } from 'react';
import { AIService } from '../services/aiService';
import { SessionInfo, SessionStatus, AIMessageChunk } from '../types/ai';

export function useAISession(aiService: AIService | undefined, userId: string) {

  // Keep status in sync with AIService (polling)
  useEffect(() => {
    if (!aiService) return;
    const interval = setInterval(() => {
      const newStatus = aiService.getStatus && aiService.getStatus();
      setStatus((prev: SessionStatus) => {
        if (prev !== newStatus) {
          console.log('[useAISession] Status changed:', prev, '->', newStatus);
          return newStatus;
        }
        return prev;
      });
    }, 200);
    return () => clearInterval(interval);
  }, [aiService]);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [status, setStatus] = useState<SessionStatus>(SessionStatus.Idle);
  const [error, setError] = useState<string | null>(null);
  // Remove unused chunks state to prevent double display and confusion
  const [loading, setLoading] = useState(false);
  const aiServiceRef = useRef(aiService);


  useEffect(() => {
    aiServiceRef.current = aiService;
  }, [aiService]);

  // (Removed AI message chunk handler registration to prevent double display)

  const startSession = useCallback(async () => {
    if (!aiServiceRef.current) return;
    setLoading(true);
    setError(null);
    // setChunks([]); // removed, no longer used
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
    loading,
    startSession,
    stopSession,
    sendUserMessage,
  };
}
