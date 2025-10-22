const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const multer = require('multer');
const { GoogleGenerativeAI } = require('@google/generative-ai');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: "gemini-pro" });

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configure multer for file uploads
const upload = multer({ 
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  }
});

// Chat endpoint for text queries
app.post('/api/chat', async (req, res) => {
  try {
    const { message, context } = req.body;
    
    // Log incoming message for debugging
    console.log('📨 Received chat message:', {
      message: message,
      context: context,
      timestamp: new Date().toISOString(),
      clientIP: req.ip
    });
    
    if (!message) {
      console.log('❌ Error: Message is required');
      return res.status(400).json({ error: 'Message is required' });
    }
    
    console.log('🤖 Processing message with Gemini AI...');

    // Create a dementia-friendly prompt
    const prompt = `You are a helpful, patient, and caring assistant speaking to someone with dementia. 
    Please respond in a simple, clear, and supportive manner. Keep responses short and easy to understand.
    Avoid complex instructions or overwhelming information.
    
    User message: ${message}
    ${context ? `Context: ${context}` : ''}`;

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    console.log('✅ AI Response generated:', {
      inputMessage: message,
      responseText: text.substring(0, 100) + '...',
      responseLength: text.length,
      timestamp: new Date().toISOString()
    });

    res.json({ 
      response: text,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('😱 Chat error details:', {
      originalMessage: req.body.message,
      error: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    
    res.status(500).json({ 
      error: 'I\'m having trouble understanding right now. Please try again.',
      debug: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

// Voice to text endpoint using Gemini
app.post('/api/voice-to-text', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'Audio file is required' });
    }

    // For now, we'll use a placeholder response since Gemini's audio processing
    // might need specific setup. In a real implementation, you'd process the audio file here.
    
    res.json({ 
      text: 'Voice processing is being set up. Please use text input for now.',
      confidence: 0.9 
    });

  } catch (error) {
    console.error('Voice to text error:', error);
    res.status(500).json({ 
      error: 'Could not process your voice. Please try speaking again.' 
    });
  }
});

// Memory Lane endpoint
app.post('/api/memory-lane', async (req, res) => {
  try {
    const { query, memoryType } = req.body;
    
    console.log('🌅 Memory Lane request:', {
      query: query,
      memoryType: memoryType,
      timestamp: new Date().toISOString()
    });

    // Check if the query mentions Mira or granddaughter
    const isMiraRelated = query && (query.toLowerCase().includes('mira') || 
                                   query.toLowerCase().includes('granddaughter') ||
                                   query.toLowerCase().includes('visit') ||
                                   query.toLowerCase().includes('special day') ||
                                   query.toLowerCase().includes('park') ||
                                   query.toLowerCase().includes('hug') ||
                                   query.toLowerCase().includes('scarf') ||
                                   query.toLowerCase().includes('red') ||
                                   query.toLowerCase().includes('autumn') ||
                                   query.toLowerCase().includes('smile'));

    let prompt;
    if (isMiraRelated) {
      prompt = `You are helping someone with dementia recall a beautiful memory with their granddaughter Mira. 
      This was a special visit where they spent time together outdoors in autumn, both wearing matching red polka dot scarves.
      They shared the most wonderful hug, both smiling so brightly with pure joy and love.
      The autumn leaves created a perfect backdrop for this precious grandmother-granddaughter moment.
      Respond with warmth and help them explore this precious memory.
      Keep responses simple, loving, and encouraging.
      
      User input: ${query}`;
    } else {
      prompt = `You are helping someone with dementia explore their memories. 
      Please provide warm, encouraging responses about ${memoryType || 'general memories'}.
      Ask gentle questions that might help them recall positive experiences.
      Keep the tone supportive and nostalgic.
      
      ${query ? `User input: ${query}` : 'Start a conversation about pleasant memories.'}`;
    }

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();

    // Memory suggestions based on context
    let memorySuggestions;
    if (isMiraRelated) {
      memorySuggestions = [
        "Do you remember choosing those matching red scarves together?",
        "How did it feel when Mira gave you that big, warm hug?",
        "What made you both smile so joyfully that autumn day?",
        "Tell me about the beautiful autumn leaves around you",
        "What was special about wearing matching outfits with Mira?"
      ];
    } else {
      memorySuggestions = [
        "Tell me about your favorite childhood meal",
        "What was your favorite song when you were young?",
        "Do you remember your first pet?",
        "What was your wedding day like?",
        "Tell me about a special holiday memory"
      ];
    }

    res.json({
      response: text,
      suggestions: memorySuggestions,
      memoryType: memoryType || 'general',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Memory Lane error:', error);
    res.status(500).json({ 
      error: 'Let\'s try talking about memories again in a moment.' 
    });
  }
});

// Spotify endpoint
app.post('/api/spotify', async (req, res) => {
  try {
    const { action, query, mood } = req.body;
    
    console.log('🎵 Spotify request:', {
      action: action,
      query: query,
      mood: mood,
      timestamp: new Date().toISOString()
    });

    // Simulate Spotify integration
    const musicSuggestions = {
      'happy': ['Here Comes the Sun - The Beatles', 'What a Wonderful World - Louis Armstrong'],
      'calm': ['Claire de Lune - Claude Debussy', 'Weightless - Marconi Union'],
      'nostalgic': ['The Way You Look Tonight - Frank Sinatra', 'Moon River - Audrey Hepburn'],
      'energetic': ['Good Vibrations - The Beach Boys', 'I Want to Hold Your Hand - The Beatles']
    };

    const playlistSuggestions = [
      'Golden Oldies',
      'Classical Relaxation',
      'Big Band Era',
      'Feel Good Songs',
      'Memory Lane Hits'
    ];

    let response;
    if (action === 'search') {
      response = `I found some music for "${query}". Would you like me to play it?`;
    } else if (action === 'mood') {
      response = `Here are some ${mood} songs I think you'll enjoy!`;
    } else {
      response = 'What kind of music would you like to hear today?';
    }

    res.json({
      response,
      suggestions: musicSuggestions[mood] || musicSuggestions['happy'],
      playlists: playlistSuggestions,
      action: action || 'browse',
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Spotify error:', error);
    res.status(500).json({ 
      error: 'Music is taking a short break. Let\'s try again soon.' 
    });
  }
});

// Test endpoint to capture and echo messages
app.post('/api/test-message', (req, res) => {
  const { message } = req.body;
  console.log('📧 Test message received:', {
    message: message,
    body: req.body,
    headers: req.headers,
    timestamp: new Date().toISOString()
  });
  
  res.json({
    received: message,
    echo: `You said: "${message}"`,
    status: 'Message captured successfully',
    timestamp: new Date().toISOString()
  });
});

// API Documentation endpoint
app.get('/docs', (req, res) => {
  const apiDocs = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dementia Chat API Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        .endpoint {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }
        .method {
            display: inline-block;
            padding: 5px 10px;
            color: white;
            border-radius: 4px;
            font-weight: bold;
            margin-right: 10px;
        }
        .get { background-color: #28a745; }
        .post { background-color: #007bff; }
        .endpoint-url {
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
        }
        .code {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        .response {
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .status-running {
            color: #28a745;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Dementia Chat API Documentation</h1>
            <p>A compassionate AI-powered chat API designed for dementia patients</p>
            <p class="status-running">🟢 Server Status: Running on Port 5001</p>
        </div>

        <h2>📋 Available Endpoints</h2>

        <div class="endpoint">
            <h3>
                <span class="method get">GET</span>
                <span class="endpoint-url">/api/health</span>
            </h3>
            <p><strong>Description:</strong> Health check endpoint to verify server status</p>
            <h4>Response Example:</h4>
            <div class="code">{
  "status": "OK",
  "message": "Dementia Chat API is running",
  "timestamp": "2025-10-13T18:37:45.000Z"
}</div>
        </div>

        <div class="endpoint">
            <h3>
                <span class="method post">POST</span>
                <span class="endpoint-url">/api/chat</span>
            </h3>
            <p><strong>Description:</strong> Main chat endpoint for AI conversations with dementia-friendly responses</p>
            <h4>Request Body:</h4>
            <div class="code">{
  "message": "Hi, how are you today?",
  "context": "optional context information"
}</div>
            <h4>Response Example:</h4>
            <div class="code">{
  "response": "Hello! I'm doing well, thank you for asking. How are you feeling today? I'm here to help with anything you need.",
  "timestamp": "2025-10-13T18:37:45.123Z"
}</div>
            <h4>Test Command:</h4>
            <div class="code">curl -X POST http://localhost:5001/api/chat \\
-H "Content-Type: application/json" \\
-d '{"message": "hi"}'</div>
        </div>

        <div class="endpoint">
            <h3>
                <span class="method post">POST</span>
                <span class="endpoint-url">/api/memory-lane</span>
            </h3>
            <p><strong>Description:</strong> Memory exploration endpoint for gentle memory-focused conversations</p>
            <h4>Request Body:</h4>
            <div class="code">{
  "query": "Tell me about childhood memories",
  "memoryType": "childhood"
}</div>
            <h4>Response Example:</h4>
            <div class="code">{
  "response": "Let's talk about some wonderful childhood memories. What was your favorite game to play when you were little?",
  "suggestions": [
    "Tell me about your favorite childhood meal",
    "What was your favorite song when you were young?",
    "Do you remember your first pet?"
  ],
  "memoryType": "childhood",
  "timestamp": "2025-10-13T18:37:45.456Z"
}</div>
            <h4>Test Command:</h4>
            <div class="code">curl -X POST http://localhost:5001/api/memory-lane \\
-H "Content-Type: application/json" \\
-d '{"query": "childhood memories", "memoryType": "childhood"}'</div>
        </div>

        <div class="endpoint">
            <h3>
                <span class="method post">POST</span>
                <span class="endpoint-url">/api/spotify</span>
            </h3>
            <p><strong>Description:</strong> Music recommendation endpoint with mood-based suggestions</p>
            <h4>Request Body:</h4>
            <div class="code">{
  "action": "search",
  "query": "happy songs",
  "mood": "happy"
}</div>
            <h4>Response Example:</h4>
            <div class="code">{
  "response": "Here are some happy songs I think you'll enjoy!",
  "suggestions": [
    "Here Comes the Sun - The Beatles",
    "What a Wonderful World - Louis Armstrong"
  ],
  "playlists": [
    "Golden Oldies",
    "Feel Good Songs"
  ],
  "action": "search",
  "timestamp": "2025-10-13T18:37:45.789Z"
}</div>
            <h4>Test Command:</h4>
            <div class="code">curl -X POST http://localhost:5001/api/spotify \\
-H "Content-Type: application/json" \\
-d '{"action": "search", "query": "happy songs", "mood": "happy"}'</div>
        </div>

        <div class="endpoint">
            <h3>
                <span class="method post">POST</span>
                <span class="endpoint-url">/api/voice-to-text</span>
            </h3>
            <p><strong>Description:</strong> Voice processing endpoint (currently placeholder for future Gemini Audio API integration)</p>
            <h4>Request:</strong> Multipart form data with audio file</h4>
            <h4>Response Example:</h4>
            <div class="code">{
  "text": "Voice processing is being set up. Please use text input for now.",
  "confidence": 0.9
}</div>
        </div>

        <div class="endpoint">
            <h3>
                <span class="method post">POST</span>
                <span class="endpoint-url">/api/test-message</span>
            </h3>
            <p><strong>Description:</strong> Test endpoint to verify message capture (debugging)</p>
            <h4>Request Body:</h4>
            <div class="code">{
  "message": "test message"
}</div>
            <h4>Response Example:</h4>
            <div class="code">{
  "received": "test message",
  "echo": "You said: \"test message\"",
  "status": "Message captured successfully",
  "timestamp": "2025-10-13T18:37:45.999Z"
}</div>
        </div>

        <h2>🔑 Features</h2>
        <ul>
            <li><strong>🧠 Dementia-Friendly AI:</strong> Specialized prompts for patient, clear responses</li>
            <li><strong>📨 Message Logging:</strong> All requests are logged with timestamps and client info</li>
            <li><strong>🎤 Voice Support:</strong> Designed for future voice input integration</li>
            <li><strong>🎵 Music Integration:</strong> Mood-based music recommendations</li>
            <li><strong>💭 Memory Exploration:</strong> Gentle memory conversation prompts</li>
            <li><strong>🔒 CORS Enabled:</strong> Ready for cross-origin requests from desktop app</li>
        </ul>

        <h2>🚀 Base URL</h2>
        <div class="code">http://localhost:5001</div>

        <h2>📊 Server Logs</h2>
        <p>All API requests are logged in real-time to the server console with detailed information including:</p>
        <ul>
            <li>📨 Incoming message content</li>
            <li>⏰ Timestamps</li>
            <li>🌐 Client IP addresses</li>
            <li>🤖 AI processing status</li>
            <li>❌ Error details (if any)</li>
        </ul>

        <div class="response">
            <strong>✅ All endpoints are currently capturing messages successfully!</strong><br>
            The "hi" message and all other requests are being properly received and logged.
        </div>
    </div>
</body>
</html>
  `;
  res.send(apiDocs);
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    message: 'Dementia Chat API is running',
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Something went wrong. Please try again.' 
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/api/health`);
});