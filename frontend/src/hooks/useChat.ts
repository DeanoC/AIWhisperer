
import { useState, useCallback, useRef } from 'react';
import { ChatMessage, MessageSender } from '../types/chat';
import { MessageStatus } from '../types/ai';
import { AIMessageChunk } from '../types/ai';
import { Agent } from '../types/agent';


export interface ChatOptions {
  currentAgentId?: string;
  currentAgent?: Agent;
}

export function useChat(options?: ChatOptions) {
  const finalized = useRef(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentAIMessage, setCurrentAIMessage] = useState<string>('');
  // Track a unique ID for the current streaming AI message
  const currentAIMessageId = useRef<string | null>(null);
  const currentAgent = options?.currentAgent;

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
    finalized.current = false;
  }, []);

  // Append a chunk to the current AI message
  const appendAIChunk = useCallback((chunk: AIMessageChunk) => {
    if (finalized.current) return; // Prevent double-finalizing
    console.log('[useChat.appendAIChunk] called with:', chunk);
    setCurrentAIMessage((prev) => {
      const next = prev + (chunk.content || '');
      if (chunk.isFinal) {
        if (next.trim()) {
          const msg: ChatMessage = {
            id: currentAIMessageId.current || `${Date.now()}-ai-${Math.random().toString(36).slice(2, 8)}`,
            sender: MessageSender.AI,
            content: next,
            timestamp: new Date().toISOString(),
            status: MessageStatus.Received,
            metadata: currentAgent ? { 
              agentId: currentAgent.id, 
              agent: currentAgent 
            } : undefined,
          };
          setMessages((prevMsgs) => {
            if (prevMsgs.some(m => m.id === msg.id)) {
              console.log('[useChat] Duplicate AI message prevented:', msg.id);
              return prevMsgs;
            }
            console.log('[useChat] Adding AI message to chat:', msg);
            return [...prevMsgs, msg];
          });
        }
        setLoading(false);
        currentAIMessageId.current = null;
        finalized.current = true; // Mark as finalized
        return '';
      }
      return next;
    });
  }, [currentAgent]);

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

  // Function to update agent metadata for messages that don't have it
  const updateMessageAgent = useCallback((messageId: string, agent: Agent) => {
    setMessages(prevMessages => 
      prevMessages.map(msg => {
        if (msg.id === messageId && msg.sender === MessageSender.AI && !msg.metadata?.agent) {
          return {
            ...msg,
            metadata: {
              ...msg.metadata,
              agentId: agent.id,
              agent: agent
            }
          };
        }
        return msg;
      })
    );
  }, []);

  return {
    messages,
    loading,
    currentAIMessage,
    addUserMessage,
    startAIMessage,
    appendAIChunk,
    addSystemMessage,
    updateMessageAgent,
  };
}
