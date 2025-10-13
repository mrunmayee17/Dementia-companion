# 🧠 Dementia Companion

> A compassionate desktop chat application designed specifically for people with dementia, featuring voice input, AI conversations, memory exploration, and music integration.

![Desktop App](https://img.shields.io/badge/Platform-Desktop-blue)
![Electron](https://img.shields.io/badge/Electron-Latest-brightgreen)
![React](https://img.shields.io/badge/React-18+-blue)
![Node.js](https://img.shields.io/badge/Node.js-18+-green)
![AI Powered](https://img.shields.io/badge/AI-Gemini%20Powered-yellow)

## 🎯 Purpose

This application provides a dementia-friendly chat interface with large buttons, clear fonts, and AI responses specifically designed to be patient, supportive, and easy to understand.

## Features

- **Dementia-Friendly Design**: Large buttons, high contrast colors, and clear fonts
- **Voice Input**: Browser-based speech recognition for easy communication
- **Three Modes**:
  - **Chat**: General conversation with AI assistant
  - **Memory Lane**: Guided conversations about memories and experiences
  - **Music**: Spotify integration for music discovery and playback
- **Accessibility**: Responsive design with high contrast mode support
- **AI-Powered**: Uses Gemini API for intelligent, patient responses

## Technology Stack

### Backend
- Node.js with Express
- Gemini AI API for chat responses
- CORS enabled for cross-origin requests
- Multer for file handling (voice uploads)

### Frontend
- React with TypeScript
- Browser Speech Recognition API
- Axios for API communication
- React Icons for UI elements
- Responsive CSS with accessibility features

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- Modern web browser with speech recognition support

### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:mrunmayee17/Dementia-companion.git
   cd Dementia-companion
   ```

2. **Install dependencies for all parts:**
   ```bash
   npm run install-all
   ```

3. **Configure environment variables:**
   ```bash
   # Copy the template file
   cp server/.env.template server/.env
   
   # Edit the .env file and add your API keys
   # Get Gemini API key from: https://aistudio.google.com/app/apikey
   ```
   
   Update `server/.env` with your keys:
   ```env
   PORT=5001
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here  # Optional
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here  # Optional
   ```

4. **Start the desktop application:**
   ```bash
   ./launch-desktop.sh
   ```

   Or manually:
   ```bash
   # Start server first
   cd server && node index.js &
   
   # Then start desktop app
   cd ../client && npm run electron
   ```

   The server runs on port 5001 and the desktop app loads locally.

### Manual Setup (Alternative)

If the above doesn't work, you can start each part manually:

1. **Start the backend:**
   ```bash
   cd server
   npm install
   npm start
   ```

2. **Start the frontend (in a new terminal):**
   ```bash
   cd client
   npm install
   npm start
   ```

## Usage Guide

### For Caregivers/Setup

1. **Accessing the Application:**
   - Open a web browser and go to `http://localhost:3000`
   - Ensure microphone permissions are granted for voice input

2. **Browser Compatibility:**
   - Chrome, Edge, and Safari work best for speech recognition
   - Firefox has limited speech recognition support

### For Users with Dementia

1. **Chat Mode:**
   - Ask any questions or have a conversation
   - The AI responds with simple, clear language
   - Use voice or type messages

2. **Memory Lane:**
   - Explore memories from the past
   - The AI asks gentle, guiding questions
   - Share stories about family, childhood, or special moments

3. **Music Mode:**
   - Ask for songs by name or describe your mood
   - Get music recommendations
   - (Note: Full Spotify integration requires additional setup)

## API Endpoints

### Backend Endpoints

- `GET /api/health` - Health check
- `POST /api/chat` - General chat conversations
- `POST /api/memory-lane` - Memory-focused conversations
- `POST /api/spotify` - Music-related requests
- `POST /api/voice-to-text` - Voice processing (currently placeholder)

### Example API Usage

```javascript
// Chat request
const response = await axios.post('http://localhost:5000/api/chat', {
  message: "Hello, how are you today?"
});

// Memory Lane request
const response = await axios.post('http://localhost:5000/api/memory-lane', {
  query: "Tell me about childhood memories",
  memoryType: "childhood"
});

// Spotify request
const response = await axios.post('http://localhost:5000/api/spotify', {
  action: "search",
  query: "happy songs",
  mood: "happy"
});
```

## Customization

### Modifying AI Responses
Edit the prompts in `server/index.js` to customize how the AI responds:
- Chat responses: Line 38-44
- Memory Lane responses: Line 91-96
- Error messages throughout the file

### Styling Changes
Modify `client/src/App.css` to adjust:
- Colors and contrast
- Button sizes
- Font sizes
- Spacing and layout

### Adding New Features
1. Add new endpoints in `server/index.js`
2. Create new UI components in `client/src/`
3. Update the sidebar with new buttons

## Accessibility Features

- **Large Buttons**: Easy to press for users with motor difficulties
- **High Contrast**: Better visibility for users with vision issues
- **Simple Language**: AI trained to use clear, simple responses
- **Voice Input**: Alternative to typing for users with dexterity issues
- **Responsive Design**: Works on tablets and mobile devices
- **Error Handling**: Gentle error messages that don't cause confusion

## Development Notes

### Voice Recognition
- Uses browser's built-in Speech Recognition API
- Falls back gracefully if not supported
- Provides clear error messages for common issues

### AI Integration
- Gemini API configured with dementia-specific prompts
- Responses are kept short and simple
- Error handling prevents overwhelming users

### Security
- API keys stored in environment variables
- CORS configured for local development
- Input validation on all endpoints

## Troubleshooting

### Common Issues

1. **Voice not working:**
   - Check microphone permissions in browser
   - Ensure using Chrome, Edge, or Safari
   - Check if microphone is working in other applications

2. **API errors:**
   - Verify Gemini API key is correct
   - Check server is running on port 5000
   - Look at browser console for error messages

3. **Styling issues:**
   - Clear browser cache
   - Check if CSS file is loading properly
   - Verify React development server is running

### Getting Help

Check the browser console (F12) for error messages. Most issues will be logged there with helpful information.

## Future Enhancements

- Full Spotify Web API integration
- Photo memory sharing
- Voice recognition improvements with Gemini Audio API
- Caregiver dashboard for monitoring usage
- Offline mode for basic functionality
- Multiple language support

## License

MIT License - feel free to modify and use for your needs.