import { useState, useCallback } from 'react';
import { ChatMessage, MessageSender } from '../types/chat';
import { MessageStatus } from '../types/ai';
import { AIMessageChunk } from '../types/ai';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentAIMessage, setCurrentAIMessage] = useState<string>('');

  // Add a user message
  const addUserMessage = useCallback((content: string) => {
    const msg: ChatMessage = {
      id: `${Date.now()}-user`,
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
  }, []);

  // Append a chunk to the current AI message
  const appendAIChunk = useCallback((chunk: AIMessageChunk) => {
    setCurrentAIMessage((prev) => {
      const next = prev + (chunk.content || '');
      if (chunk.isFinal) {
        const msg: ChatMessage = {
          id: `${Date.now()}-ai`,
          sender: MessageSender.AI,
          content: next,
          timestamp: new Date().toISOString(),
          status: MessageStatus.Received,
        };
        setMessages((prevMsgs) => [...prevMsgs, msg]);
        setLoading(false);
        return '';
      }
      return next;
    });
  }, []);

  // Add a system message
  const addSystemMessage = useCallback((content: string) => {
    const msg: ChatMessage = {
      id: `${Date.now()}-sys`,
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
