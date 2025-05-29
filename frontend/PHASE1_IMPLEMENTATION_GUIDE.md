# Phase 1: Quick Implementation Guide

## Starting Point: AIService Agent Methods

### 1. First Test File to Create: `aiService.agent.test.ts`

```typescript
import { AIService } from '../aiService';
import { JsonRpcService } from '../jsonRpcService';

describe('AIService Agent Methods', () => {
  let aiService: AIService;
  let mockJsonRpcService: jest.Mocked<JsonRpcService>;
  
  beforeEach(() => {
    mockJsonRpcService = {
      request: jest.fn(),
      // ... other mocked methods
    } as any;
    
    aiService = new AIService(mockJsonRpcService);
  });
  
  describe('listAgents', () => {
    it('should return array of available agents', async () => {
      const mockAgents = [
        { id: 'P', name: 'Patricia', role: 'Planner' },
        { id: 'T', name: 'Tessa', role: 'Tester' }
      ];
      
      mockJsonRpcService.request.mockResolvedValue(mockAgents);
      
      const agents = await aiService.listAgents();
      
      expect(mockJsonRpcService.request).toHaveBeenCalledWith('agent.list', {});
      expect(agents).toEqual(mockAgents);
    });
  });
  
  // Continue with other methods...
});
```

### 2. Implementation in `aiService.ts`

After writing all tests, implement:

```typescript
export class AIService {
  async listAgents(): Promise<Agent[]> {
    return this.jsonRpcService.request('agent.list', {});
  }
  
  async switchAgent(agentId: string): Promise<void> {
    await this.jsonRpcService.request('session.switch_agent', { 
      agent_id: agentId 
    });
  }
  
  async getCurrentAgent(): Promise<string> {
    return this.jsonRpcService.request('session.current_agent', {});
  }
  
  async handoffToAgent(agentId: string, context: any): Promise<void> {
    await this.jsonRpcService.request('session.handoff', {
      agent_id: agentId,
      context
    });
  }
}
```

### 3. Type Definitions to Add

In `types/agent.ts`:
```typescript
export interface Agent {
  id: string;
  name: string;
  role: string;
  description?: string;
  color: string;
  icon?: string;
  status?: 'online' | 'busy' | 'offline';
}

export interface AgentHandoffContext {
  task?: string;
  files?: string[];
  previousAgent?: string;
  metadata?: Record<string, any>;
}
```

### 4. Update Existing Code

Replace in `App.tsx`:
```typescript
// OLD:
await aiService.dispatchCommand(`/session.switch_agent {"agent_id":"${agentId}"}`);

// NEW:
await aiService.switchAgent(agentId);
```

## Quick Win Implementation Order

1. **Start with simplest test**: `getCurrentAgent()` - just returns a string
2. **Then**: `listAgents()` - returns array, easy to mock
3. **Then**: `switchAgent()` - void return, just verify the call
4. **Finally**: `handoffToAgent()` - most complex with context parameter

## Running Tests Continuously

```bash
cd frontend
npm test -- --watch aiService.agent.test.ts
```

This will re-run tests as you implement, giving immediate feedback.

## Next Steps After Phase 1

Once all AIService tests pass:
1. Integration test with real WebSocket
2. Update all components using the old command system
3. Move to Phase 2: Agent UI components