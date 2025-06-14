import { useState, useCallback, useEffect } from 'react';
import { AIService } from '../services/aiService';
import { ChannelMessage, ChannelType, ChannelVisibilityPreferences, isChannelVisible } from '../types/channel';

interface UseChannelsResult {
  channelMessages: ChannelMessage[];
  visibilityPreferences: ChannelVisibilityPreferences;
  visibleMessages: ChannelMessage[];
  updateVisibility: (preferences: ChannelVisibilityPreferences) => Promise<void>;
  clearChannelMessages: () => void;
}

export function useChannels(aiService?: AIService): UseChannelsResult {
  const [channelMessages, setChannelMessages] = useState<ChannelMessage[]>([]);
  const [visibilityPreferences, setVisibilityPreferences] = useState<ChannelVisibilityPreferences>({
    showCommentary: true,
    showAnalysis: false
  });

  // Load preferences from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('channelVisibility');
    if (saved) {
      try {
        const prefs = JSON.parse(saved);
        setVisibilityPreferences(prefs);
      } catch (e) {
        console.error('Failed to load channel visibility preferences:', e);
      }
    }
  }, []);

  // Handle incoming channel messages
  useEffect(() => {
    if (!aiService) return;

    const handleChannelMessage = (message: ChannelMessage) => {
      console.log('[useChannels] Received channel message:', message);
      
      // Special handling for streaming updates (marked with isStreaming flag or sequence -1)
      if (message.metadata.isStreaming || (message.metadata.isPartial && message.metadata.sequence === -1)) {
        // This is a streaming update - find and update the most recent streaming message for this channel/agent
        setChannelMessages(prev => {
          const existingIndex = prev.findIndex(
            m => (m.metadata.isStreaming || m.metadata.sequence === -1) && 
                 m.metadata.agentId === message.metadata.agentId &&
                 m.channel === message.channel
          );
          
          if (existingIndex !== -1) {
            // Update existing streaming message
            const updated = [...prev];
            updated[existingIndex] = message;
            return updated;
          } else {
            // Add new streaming message
            return [...prev, message];
          }
        });
      } else if (message.metadata.isPartial) {
        // Regular partial message with proper sequence
        setChannelMessages(prev => {
          const existingIndex = prev.findIndex(
            m => m.metadata.sequence === message.metadata.sequence && 
                 m.channel === message.channel
          );
          
          if (existingIndex !== -1) {
            // Update existing partial message
            const updated = [...prev];
            updated[existingIndex] = message;
            return updated;
          } else {
            // Add new partial message
            return [...prev, message];
          }
        });
      } else {
        // Final message - replace any streaming message for this agent/channel or add new
        setChannelMessages(prev => {
          // First try to find exact sequence match
          let existingIndex = prev.findIndex(
            m => m.metadata.sequence === message.metadata.sequence && 
                 m.channel === message.channel
          );
          
          // If no exact sequence match, look for streaming message to replace
          if (existingIndex === -1) {
            existingIndex = prev.findIndex(
              m => (m.metadata.isStreaming || m.metadata.sequence === -1) && 
                   m.metadata.agentId === message.metadata.agentId &&
                   m.channel === message.channel
            );
          }
          
          if (existingIndex !== -1) {
            const updated = [...prev];
            updated[existingIndex] = message;
            return updated;
          } else {
            return [...prev, message];
          }
        });
      }
    };

    aiService.onChannelMessage(handleChannelMessage);

    return () => {
      aiService.onChannelMessage(() => {}); // Clear handler
    };
  }, [aiService]);

  // Update visibility preferences
  const updateVisibility = useCallback(async (preferences: ChannelVisibilityPreferences) => {
    setVisibilityPreferences(preferences);
    localStorage.setItem('channelVisibility', JSON.stringify(preferences));
    
    // Update backend if service is available
    if (aiService) {
      try {
        await aiService.updateChannelVisibility(preferences);
      } catch (error) {
        console.error('Failed to update channel visibility on backend:', error);
      }
    }
  }, [aiService]);

  // Filter messages based on visibility
  const visibleMessages = channelMessages.filter(msg => 
    isChannelVisible(msg.channel, visibilityPreferences)
  );

  // Clear all channel messages
  const clearChannelMessages = useCallback(() => {
    setChannelMessages([]);
  }, []);

  return {
    channelMessages,
    visibilityPreferences,
    visibleMessages,
    updateVisibility,
    clearChannelMessages
  };
}