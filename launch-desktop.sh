#!/bin/bash

echo "🚀 Starting Chat Helper Desktop App..."

# Navigate to project directory
cd /Users/mrunmayeerane/Desktop/Mrun/hackathon/NVhack2

# Check if server is running
if ! curl -s http://localhost:5001/api/health > /dev/null; then
    echo "Starting backend server..."
    cd server && node index.js &
    SERVER_PID=$!
    echo "Server started with PID: $SERVER_PID"
    sleep 3
else
    echo "✅ Server is already running"
fi

# Launch Electron app
echo "🖥️  Starting desktop application..."
cd /Users/mrunmayeerane/Desktop/Mrun/hackathon/NVhack2/client
npm run electron

echo "👋 Desktop app closed"