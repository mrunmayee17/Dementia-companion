import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
// Temporarily removing icons for desktop build
import { voiceService } from './services/voiceService';
import './App.css';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

interface ChatResponse {
  response: string;
  timestamp: string;
}

const API_BASE_URL = 'http://localhost:5001/api';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeMode, setActiveMode] = useState<'chat' | 'memory' | 'spotify'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message
    const welcomeMessage: Message = {
      id: '1',
      text: 'Hello! I\'m here to help you. You can chat with me, explore memories, or listen to music. How can I help you today?',
      isUser: false,
      timestamp: new Date()
    };
    setMessages([welcomeMessage]);
  }, []);

  const addMessage = (text: string, isUser: boolean) => {
    const message: Message = {
      id: Date.now().toString(),
      text,
      isUser,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = inputText.trim();
    setInputText('');
    addMessage(userMessage, true);
    setIsLoading(true);

    try {
      let endpoint = '';
      let payload: any = {};

      switch (activeMode) {
        case 'chat':
          endpoint = '/chat';
          payload = { message: userMessage };
          break;
        case 'memory':
          endpoint = '/memory-lane';
          payload = { query: userMessage };
          break;
        case 'spotify':
          endpoint = '/spotify';
          payload = { action: 'search', query: userMessage };
          break;
      }

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
      const data: ChatResponse = response.data;
      addMessage(data.response, false);

      // Add suggestions if available
      if (response.data.suggestions && response.data.suggestions.length > 0) {
        const suggestionsText = `Here are some suggestions:\n${response.data.suggestions.join('\n')}`;
        addMessage(suggestionsText, false);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      addMessage('I\'m sorry, I\'m having trouble right now. Please try again in a moment.', false);
    }

    setIsLoading(false);
  };

  const startRecording = async () => {
    if (!voiceService.isSupported()) {
      addMessage('Voice recognition is not supported in your browser. Please try typing instead.', false);
      return;
    }

    try {
      setIsRecording(true);
      setIsLoading(true);
      
      const transcript = await voiceService.startListening();
      
      if (transcript.trim()) {
        setInputText(transcript);
        addMessage('I heard: "' + transcript + '"', false);
      }
      
    } catch (error) {
      console.error('Voice recognition error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Voice recognition failed';
      addMessage(errorMessage, false);
    } finally {
      setIsRecording(false);
      setIsLoading(false);
    }
  };

  const stopRecording = () => {
    voiceService.stopListening();
    setIsRecording(false);
    setIsLoading(false);
  };

  const handleModeChange = (mode: 'chat' | 'memory' | 'spotify') => {
    setActiveMode(mode);
    let modeMessage = '';
    switch (mode) {
      case 'chat':
        modeMessage = 'Ready to chat! Ask me anything you\'d like to know.';
        break;
      case 'memory':
        modeMessage = 'Let\'s explore some wonderful memories together. What would you like to remember?';
        break;
      case 'spotify':
        modeMessage = 'Time for some music! What songs would you like to hear today?';
        break;
    }
    addMessage(modeMessage, false);
  };

  return (
    <div className="app">
      <div className="sidebar">
        <div className="sidebar-header">
          <h2>Chat Helper</h2>
        </div>
        
        <div className="sidebar-buttons">
          <button 
            className={`sidebar-btn ${activeMode === 'chat' ? 'active' : ''}`}
            onClick={() => handleModeChange('chat')}
          >
💬 Chat
          </button>
          
          <button 
            className={`sidebar-btn ${activeMode === 'memory' ? 'active' : ''}`}
            onClick={() => handleModeChange('memory')}
          >
🌅 Memory Lane
          </button>
          
          <button 
            className={`sidebar-btn ${activeMode === 'spotify' ? 'active' : ''}`}
            onClick={() => handleModeChange('spotify')}
          >
🎵 Music
          </button>
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-header">
          <h1>{activeMode === 'chat' ? 'Chat' : activeMode === 'memory' ? 'Memory Lane' : 'Music'}</h1>
        </div>

        <div className="messages-container">
          {messages.map((message) => (
            <div key={message.id} className={`message ${message.isUser ? 'user' : 'assistant'}`}>
              <div className="message-content">
                {message.text.split('\n').map((line, index) => (
                  <div key={index}>{line}</div>
                ))}
              </div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your message here..."
              className="text-input"
              disabled={isLoading}
            />
            
            <button
              onClick={isRecording ? stopRecording : startRecording}
              className={`voice-btn ${isRecording ? 'recording' : ''}`}
              disabled={isLoading}
            >
              {isRecording ? '🛑' : '🎤'}
            </button>
            
            <button
              onClick={handleSendMessage}
              className="send-btn"
              disabled={!inputText.trim() || isLoading}
            >
              ✈️
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
