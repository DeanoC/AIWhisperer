import React from 'react';
import { render, act } from '@testing-library/react';
import { useAISession } from './useAISession';
import { AIService } from '../services/aiService';
import { SessionStatus } from '../types/ai';

function setupMockAIService() {
  let chunkHandler: any = null;
  const aiService = {
    startSession: jest.fn().mockResolvedValue({ id: 'abc', status: 1, startedAt: 'now', model: 'gpt-test' }),
    stopSession: jest.fn().mockResolvedValue(undefined),
    sendUserMessage: jest.fn().mockResolvedValue('msg-1'),
    onAIMessageChunk: jest.fn((handler) => { chunkHandler = handler; }),
    getStatus: jest.fn(() => 1),
    getSessionInfo: jest.fn(() => ({ id: 'abc', status: 1, startedAt: 'now', model: 'gpt-test' })),
    getError: jest.fn(() => null),
  };
  return { aiService, getChunkHandler: () => chunkHandler };
}

describe('useAISession', () => {
  function setupTest(aiService: any) {
    let hookValue: any;
    function TestComponent() {
      const value = useAISession(aiService as any, 'user1');
      React.useEffect(() => { hookValue = value; });
      return <div />;
    }
    render(<TestComponent />);
    return () => hookValue;
  }

  it('starts a session and updates state', async () => {
    const { aiService } = setupMockAIService();
    const getHook = setupTest(aiService);
    await act(async () => {
      await getHook().startSession();
    });
    expect(getHook().sessionInfo?.id).toBe('abc');
    expect(getHook().status).toBe(1);
    expect(getHook().loading).toBe(false);
  });

  // Test removed: useAISession doesn't handle chunks directly
  // Chunk handling is done by useChat hook in the App component

  it('handles errors from startSession', async () => {
    const { aiService } = setupMockAIService();
    aiService.startSession.mockRejectedValueOnce(new Error('fail'));
    const getHook = setupTest(aiService);
    await act(async () => {
      await getHook().startSession();
    });
    expect(getHook().error).toBe('fail');
  });

  it('sends a user message', async () => {
    const { aiService } = setupMockAIService();
    const getHook = setupTest(aiService);
    await act(async () => {
      await getHook().startSession();
      await getHook().sendUserMessage('hello');
    });
    expect(aiService.sendUserMessage).toHaveBeenCalledWith('hello');
  });

  it('stops a session and updates state', async () => {
    const { aiService } = setupMockAIService();
    const getHook = setupTest(aiService);
    await act(async () => {
      await getHook().startSession();
      await getHook().stopSession();
    });
    expect(getHook().status).toBe(SessionStatus.Stopped);
  });
});
