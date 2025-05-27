import { useState, useCallback, useRef } from 'react';
import { ChatMessage, MessageSender } from '../types/chat';
import { MessageStatus } from '../types/ai';
import { AIMessageChunk } from '../types/ai';


export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentAIMessage, setCurrentAIMessage] = useState<string>('');
  // Track a unique ID for the current streaming AI message
  const currentAIMessageId = useRef<string | null>(null);

  // Add a user message
  const addUserMessage = useCallback((content: string) => {
    const msg: ChatMessage = {
      id: `${Date.now()}-user-${Math.random().toString(36).slice(2, 8)}`,
      sender: MessageSender.User,
      content,
      timestamp: new Date().toISOString(),
      status: MessageStatus.Sent,
    };
    setMessages((prev) => [...prev, msg]);
  }, []);

  // Start a new AI message (for streaming)
  const startAIMessage = useCallback(() => {
    setCurrentAIMessage('');
    setLoading(true);
    // Generate a unique ID for this AI message
    currentAIMessageId.current = `${Date.now()}-ai-${Math.random().toString(36).slice(2, 8)}`;
  }, []);

  // Append a chunk to the current AI message
  const appendAIChunk = useCallback((chunk: AIMessageChunk) => {
    setCurrentAIMessage((prev) => {
      const next = prev + (chunk.content || '');
      if (chunk.isFinal) {
        // Only add the AI message if it has content
        if (next.trim()) {
          const msg: ChatMessage = {
            id: currentAIMessageId.current || `${Date.now()}-ai-${Math.random().toString(36).slice(2, 8)}`,
            sender: MessageSender.AI,
            content: next,
            timestamp: new Date().toISOString(),
            status: MessageStatus.Received,
          };
          setMessages((prevMsgs) => {
            // Prevent duplicate AI messages with the same ID
            if (prevMsgs.some(m => m.id === msg.id)) return prevMsgs;
            return [...prevMsgs, msg];
          });
        }
        setLoading(false);
        currentAIMessageId.current = null;
        return '';
      }
      return next;
    });
  }, []);

  // Add a system message
  const addSystemMessage = useCallback((content: string) => {
    const msg: ChatMessage = {
      id: `${Date.now()}-sys-${Math.random().toString(36).slice(2, 8)}`,
      sender: MessageSender.System,
      content,
      timestamp: new Date().toISOString(),
      status: MessageStatus.Received,
    };
    setMessages((prev) => [...prev, msg]);
  }, []);

  return {
    messages,
    loading,
    currentAIMessage,
    addUserMessage,
    startAIMessage,
    appendAIChunk,
    addSystemMessage,
  };
}
