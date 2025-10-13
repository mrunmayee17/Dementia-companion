#!/bin/bash

echo "🚀 Starting Chat Helper Desktop Application..."

# Kill any existing processes on port 5000
echo "Stopping any existing backend servers..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Start the backend server in the background
echo "Starting backend server..."
cd server && npm start &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for backend server to initialize..."
sleep 3

# Check if server started successfully
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Backend server is running!"
else
    echo "❌ Backend server failed to start"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

# Start the Electron desktop app
echo "Starting desktop application..."
cd ../client
ELECTRON_IS_DEV=true npm run electron

# Cleanup: Kill the server when the app closes
echo "Cleaning up..."
kill $SERVER_PID 2>/dev/null
echo "👋 Chat Helper closed successfully!"