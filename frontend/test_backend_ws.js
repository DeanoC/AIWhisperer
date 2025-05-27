// Node.js script to test backend WebSocket JSON-RPC session and message flow
const WebSocket = require('ws');

const WS_URL = 'ws://127.0.0.1:8000/ws';
const ws = new WebSocket(WS_URL);

let sessionId = null;
let msgId = 1;

ws.on('open', () => {
  console.log('WebSocket connection opened. Starting session...');
  const startSession = {
    jsonrpc: '2.0',
    id: msgId++,
    method: 'startSession',
    params: { userId: 'test_user', sessionParams: { language: 'en' } }
  };
  ws.send(JSON.stringify(startSession));
});

ws.on('message', (data) => {
  try {
    const msg = JSON.parse(data);
    console.log('Received:', msg);
    // Handle session start
    if (msg.result && msg.result.sessionId && !sessionId) {
      sessionId = msg.result.sessionId;
      console.log('Session started:', sessionId);
      // Send a user message
      const userMsg = {
        jsonrpc: '2.0',
        id: msgId++,
        method: 'sendUserMessage',
        params: { sessionId, message: 'Hello from Node.js test client!' }
      };
      ws.send(JSON.stringify(userMsg));
    }
    // Handle AI message chunk notifications
    if (msg.method === 'AIMessageChunkNotification') {
      const params = msg.params || {};
      console.log('[AI CHUNK]', params.chunk, params.isFinal ? '(final)' : '');
      if (params.isFinal) {
        console.log('Received final AI chunk. Closing session.');
        // Optionally send stopSession
        const stopSession = {
          jsonrpc: '2.0',
          id: msgId++,
          method: 'stopSession',
          params: { sessionId }
        };
        ws.send(JSON.stringify(stopSession));
      }
    }
    // Handle session stop (response)
    if (msg.result && msg.result.stopped === true) {
      console.log('Session stopped (response). Exiting script.');
      process.exit(0);
    }
    // Handle session stop (notification)
    // NOTE: If this triggers, check backend logic—ideally, backend should close the WebSocket or send a final response.
    if (msg.method === 'SessionStatusNotification' && msg.params && msg.params.status === 2) {
      console.log('Session stopped (notification). Exiting script.');
      process.exit(0);
    }
    // Handle errors
    if (msg.error) {
      console.error('JSON-RPC error:', msg.error);
      ws.close();
    }
  } catch (e) {
    console.error('Non-JSON message:', data);
  }
});

ws.on('error', (err) => {
  console.error('WebSocket error:', err);
});

ws.on('close', () => {
  console.log('WebSocket connection closed.');
  process.exit(0);
});
