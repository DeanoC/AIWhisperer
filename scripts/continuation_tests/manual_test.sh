#!/bin/bash
# Manual test script to verify conversation replay mode works

echo "Starting interactive server in background..."
python -m interactive_server.main &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 3

echo "Running simple conversation replay test..."
echo "Hello! What is 2 + 2?" | python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay -

echo "Killing server..."
kill $SERVER_PID

echo "Done"