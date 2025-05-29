import { AIService } from './aiService';
import { JsonRpcService } from './jsonRpcService';
import { Agent, AgentHandoffContext } from '../types/agent';

describe('AIService Agent Methods', () => {
  let aiService: AIService;
  let mockJsonRpcService: jest.Mocked<JsonRpcService>;
  let mockNotificationHandler: any;
  
  beforeEach(() => {
    mockJsonRpcService = {
      sendRequest: jest.fn(),
      setNotificationHandler: jest.fn(),
    } as any;
    
    aiService = new AIService(mockJsonRpcService);
    
    // Capture the notification handler
    mockNotificationHandler = mockJsonRpcService.setNotificationHandler.mock.calls[0]?.[0];
  });
  
  describe('listAgents', () => {
    it('should return array of available agents', async () => {
      const mockAgents: Agent[] = [
        { 
          id: 'P', 
          name: 'Patricia', 
          role: 'Planner',
          description: 'Creates project plans and breaks down tasks',
          color: '#8B5CF6'
        },
        { 
          id: 'T', 
          name: 'Tessa', 
          role: 'Tester',
          description: 'Writes and runs tests',
          color: '#3B82F6'
        },
        {
          id: 'D',
          name: 'David',
          role: 'Developer',
          description: 'Implements features and fixes bugs',
          color: '#F97316'
        },
        {
          id: 'R',
          name: 'Rachel',
          role: 'Reviewer',
          description: 'Reviews code and provides feedback',
          color: '#10B981'
        }
      ];
      
      mockJsonRpcService.sendRequest.mockResolvedValue(mockAgents);
      
      const agents = await aiService.listAgents();
      
      expect(mockJsonRpcService.sendRequest).toHaveBeenCalledWith('agent.list', {});
      expect(agents).toEqual(mockAgents);
    });

    it('should handle empty agent list', async () => {
      mockJsonRpcService.sendRequest.mockResolvedValue([]);
      
      const agents = await aiService.listAgents();
      
      expect(agents).toEqual([]);
    });

    it('should throw error if request fails', async () => {
      mockJsonRpcService.sendRequest.mockRejectedValue(new Error('Network error'));
      
      await expect(aiService.listAgents()).rejects.toThrow('Network error');
    });
  });
  
  describe('getCurrentAgent', () => {
    beforeEach(() => {
      // Set up a session for these tests
      (aiService as any).sessionId = 'test-session-id';
    });

    it('should return current agent ID', async () => {
      mockJsonRpcService.sendRequest.mockResolvedValue('P');
      
      const currentAgent = await aiService.getCurrentAgent();
      
      expect(mockJsonRpcService.sendRequest).toHaveBeenCalledWith('session.current_agent', {});
      expect(currentAgent).toBe('P');
    });

    it('should return null if no agent is active', async () => {
      mockJsonRpcService.sendRequest.mockResolvedValue(null);
      
      const currentAgent = await aiService.getCurrentAgent();
      
      expect(currentAgent).toBeNull();
    });

    it('should throw error if session not initialized', async () => {
      // Clear the session ID
      (aiService as any).sessionId = null;
      
      await expect(aiService.getCurrentAgent()).rejects.toThrow('Session not initialized');
    });
  });

  describe('switchAgent', () => {
    beforeEach(() => {
      // Set up a session for these tests
      (aiService as any).sessionId = 'test-session-id';
    });

    it('should switch to specified agent', async () => {
      mockJsonRpcService.sendRequest.mockResolvedValue({ success: true });
      
      await aiService.switchAgent('T');
      
      expect(mockJsonRpcService.sendRequest).toHaveBeenCalledWith('session.switch_agent', { 
        agent_id: 'T' 
      });
    });

    it('should throw error if agent not found', async () => {
      mockJsonRpcService.sendRequest.mockRejectedValue(new Error('Agent not found: X'));
      
      await expect(aiService.switchAgent('X')).rejects.toThrow('Agent not found: X');
    });

    it('should throw error if session not initialized', async () => {
      // Clear the session ID
      (aiService as any).sessionId = null;
      
      await expect(aiService.switchAgent('P')).rejects.toThrow('Session not initialized');
    });
  });

  describe('handoffToAgent', () => {
    beforeEach(() => {
      // Set up a session for these tests
      (aiService as any).sessionId = 'test-session-id';
    });

    it('should handoff to agent with context', async () => {
      const context: AgentHandoffContext = {
        task: 'Review the implementation',
        files: ['src/app.ts', 'src/utils.ts'],
        previousAgent: 'D',
        metadata: { priority: 'high' }
      };
      
      mockJsonRpcService.sendRequest.mockResolvedValue({ success: true });
      
      await aiService.handoffToAgent('R', context);
      
      expect(mockJsonRpcService.sendRequest).toHaveBeenCalledWith('session.handoff', {
        agent_id: 'R',
        context
      });
    });

    it('should handoff without context', async () => {
      mockJsonRpcService.sendRequest.mockResolvedValue({ success: true });
      
      await aiService.handoffToAgent('P');
      
      expect(mockJsonRpcService.sendRequest).toHaveBeenCalledWith('session.handoff', {
        agent_id: 'P',
        context: undefined
      });
    });

    it('should throw error if handoff fails', async () => {
      mockJsonRpcService.sendRequest.mockRejectedValue(new Error('Handoff failed'));
      
      await expect(aiService.handoffToAgent('T')).rejects.toThrow('Handoff failed');
    });

    it('should throw error if session not initialized', async () => {
      // Clear the session ID
      (aiService as any).sessionId = null;
      
      await expect(aiService.handoffToAgent('P')).rejects.toThrow('Session not initialized');
    });
  });

  describe('notification handling', () => {
    it('should handle agent_changed notification', () => {
      const handler = jest.fn();
      aiService.onAgentChanged(handler);
      
      // Simulate notification
      mockNotificationHandler({
        method: 'agent_changed',
        params: { agent_id: 'D' }
      });
      
      expect(handler).toHaveBeenCalledWith('D');
    });

    it('should handle agent_handoff notification', () => {
      const handler = jest.fn();
      aiService.onAgentHandoff(handler);
      
      // Simulate notification
      mockNotificationHandler({
        method: 'agent_handoff',
        params: {
          from_agent: 'P',
          to_agent: 'D',
          context: { task: 'Implement feature' }
        }
      });
      
      expect(handler).toHaveBeenCalledWith({
        fromAgent: 'P',
        toAgent: 'D',
        context: { task: 'Implement feature' }
      });
    });

    it('should remove notification handler', () => {
      const handler = jest.fn();
      const unsubscribe = aiService.onAgentChanged(handler);
      
      // Add handler
      expect((aiService as any).agentChangedHandlers).toContain(handler);
      
      // Remove handler
      unsubscribe();
      
      expect((aiService as any).agentChangedHandlers).not.toContain(handler);
    });

    it('should handle multiple handlers', () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();
      
      aiService.onAgentChanged(handler1);
      aiService.onAgentChanged(handler2);
      
      // Simulate notification
      mockNotificationHandler({
        method: 'agent_changed',
        params: { agent_id: 'T' }
      });
      
      expect(handler1).toHaveBeenCalledWith('T');
      expect(handler2).toHaveBeenCalledWith('T');
    });
  });

  describe('error scenarios', () => {
    it('should handle timeout errors', async () => {
      mockJsonRpcService.sendRequest.mockRejectedValue(new Error('Request timeout'));
      
      await expect(aiService.listAgents()).rejects.toThrow('Request timeout');
    });

    it('should handle malformed responses', async () => {
      mockJsonRpcService.sendRequest.mockResolvedValue('not-an-array');
      
      await expect(aiService.listAgents()).rejects.toThrow('Invalid response: expected array of agents');
    });

    it('should update error property on failure', async () => {
      mockJsonRpcService.sendRequest.mockRejectedValue(new Error('API Error'));
      
      try {
        await aiService.listAgents();
      } catch (e) {
        // Expected to throw
      }
      
      expect(aiService.getError()).toBe('API Error');
    });
  });
});