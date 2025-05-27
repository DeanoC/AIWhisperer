import React from 'react';
import { render, act } from '@testing-library/react';
import { useChat } from './useChat';
import { MessageSender } from '../types/chat';
import { MessageStatus, AIMessageChunk } from '../types/ai';

describe('useChat', () => {
  function setupTest() {
    let hookValue: any;
    function TestComponent() {
      const value = useChat();
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
});
