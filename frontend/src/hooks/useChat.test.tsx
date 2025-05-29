import React from 'react';
import { render, act } from '@testing-library/react';
import { useChat } from './useChat';
import { MessageSender } from '../types/chat';
import { MessageStatus, AIMessageChunk } from '../types/ai';
import { Agent } from '../types/agent';

describe('useChat', () => {
  function setupTest(options?: { currentAgent?: Agent }) {
    let hookValue: any;
    function TestComponent() {
      const value = useChat(options);
      React.useEffect(() => { hookValue = value; });
      return <div />;
    }
    render(<TestComponent />);
    return () => hookValue;
  }

  it('adds a user message', () => {
    const getHook = setupTest();
    act(() => {
      getHook().addUserMessage('hello');
    });
    expect(getHook().messages.length).toBe(1);
    expect(getHook().messages[0].sender).toBe(MessageSender.User);
    expect(getHook().messages[0].content).toBe('hello');
  });

  it('streams and finalizes an AI message', () => {
    const getHook = setupTest();
    act(() => {
      getHook().startAIMessage();
      getHook().appendAIChunk({ content: 'hi', index: 0, isFinal: false });
      getHook().appendAIChunk({ content: ' there', index: 1, isFinal: true });
    });
    expect(getHook().messages.length).toBe(1);
    expect(getHook().messages[0].sender).toBe(MessageSender.AI);
    expect(getHook().messages[0].content).toContain('hi there');
    expect(getHook().loading).toBe(false);
  });

  it('adds a system message', () => {
    const getHook = setupTest();
    act(() => {
      getHook().addSystemMessage('system info');
    });
    expect(getHook().messages.length).toBe(1);
    expect(getHook().messages[0].sender).toBe(MessageSender.System);
    expect(getHook().messages[0].content).toBe('system info');
  });

  it('stores agent metadata in AI messages', () => {
    const testAgent: Agent = {
      id: 'test-agent',
      name: 'Test Agent',
      role: 'tester',
      description: 'Test agent for testing',
      color: '#ff0000'
    };
    
    const getHook = setupTest({ currentAgent: testAgent });
    act(() => {
      getHook().startAIMessage();
      getHook().appendAIChunk({ content: 'hello from agent', index: 0, isFinal: true });
    });
    
    expect(getHook().messages.length).toBe(1);
    expect(getHook().messages[0].sender).toBe(MessageSender.AI);
    expect(getHook().messages[0].metadata?.agentId).toBe('test-agent');
    expect(getHook().messages[0].metadata?.agent).toEqual(testAgent);
  });

  it('can update agent metadata for existing messages', () => {
    const testAgent: Agent = {
      id: 'test-agent',
      name: 'Test Agent',
      role: 'tester',
      description: 'Test agent for testing',
      color: '#ff0000'
    };
    
    // Create a message without agent metadata first
    const getHook = setupTest();
    act(() => {
      getHook().startAIMessage();
      getHook().appendAIChunk({ content: 'hello without agent', index: 0, isFinal: true });
    });
    
    expect(getHook().messages[0].metadata).toBeUndefined();
    
    // Update the message with agent metadata
    act(() => {
      getHook().updateMessageAgent(getHook().messages[0].id, testAgent);
    });
    
    expect(getHook().messages[0].metadata?.agentId).toBe('test-agent');
    expect(getHook().messages[0].metadata?.agent).toEqual(testAgent);
  });
});
