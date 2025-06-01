#!/bin/bash
# Script to start an isolated AI Whisperer server for debugging

echo "🚀 Starting isolated AI Whisperer server for debugging..."

# Generate a random port
PORT=$(shuf -i 20000-40000 -n 1)

echo "📡 Server will start on port: $PORT"
echo "🌐 URL: http://127.0.0.1:$PORT"
echo "🔌 WebSocket: ws://localhost:$PORT/ws"
echo ""

# Set the batch port environment variable
export AIWHISPERER_BATCH_PORT=$PORT

# Start the server
echo "🎭 Starting uvicorn server..."
python -m uvicorn interactive_server.main:app --host=127.0.0.1 --port=$PORT --log-level=info

echo "✅ Server stopped"
