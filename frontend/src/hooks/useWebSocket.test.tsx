import React from 'react';
import { render, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';

describe('useWebSocket', () => {
  let wsBackup: any;
  let mockWebSocket: any;

  beforeAll(() => {
    wsBackup = global.WebSocket;
    mockWebSocket = class {
      static OPEN = 1;
      static CONNECTING = 0;
      readyState = 0;
      onopen: any;
      onclose: any;
      onerror: any;
      close = jest.fn();
      constructor() {
        setTimeout(() => { this.readyState = 1; this.onopen && this.onopen({}); }, 10);
      }
    };
    global.WebSocket = mockWebSocket;
  });

  afterAll(() => {
    global.WebSocket = wsBackup;
  });

  function TestComponent({ url }: { url: string }) {
    const { status } = useWebSocket(url);
    return <div data-testid="status">{status}</div>;
  }

  it('connects and updates status', async () => {
    const { findByTestId } = render(<TestComponent url="ws://test" />);
    const statusDiv = await findByTestId('status');
    expect(statusDiv.textContent === 'connecting' || statusDiv.textContent === 'connected').toBe(true);
  });

  it('cleans up on unmount', () => {
    const { unmount } = render(<TestComponent url="ws://test" />);
    unmount();
    // No error should occur
  });
});
