import React from 'react';
import './MemoryCapsule.css';
import miraMemoryImage from '../assets/grandma-granddaughter-activities.jpg';

interface MemoryCapsuleProps {
  onMemorySelect: (memoryPrompt: string) => void;
}

const MemoryCapsule: React.FC<MemoryCapsuleProps> = ({ onMemorySelect }) => {
  const memoryData = {
    title: "A Special Visit with Mira",
    description: "This is a beautiful memory of you and your granddaughter Mira spending time together, sharing a loving hug in the autumn park.",
    imageAlt: "Grandmother and granddaughter Mira in matching red polka dot scarves, hugging and smiling joyfully together outdoors among autumn trees",
    prompts: [
      "Tell me about this special day with Mira",
      "Do you remember wearing those matching red scarves?",
      "How did it feel to get such a big hug from Mira?",
      "What made you both smile so brightly that day?",
      "What was it like spending time together in the autumn?"
    ]
  };

  const handlePromptClick = (prompt: string) => {
    onMemorySelect(prompt);
  };

  return (
    <div className="memory-capsule">
      <div className="memory-header">
        <h2 className="memory-title">{memoryData.title}</h2>
        <p className="memory-description">{memoryData.description}</p>
      </div>
      
      <div className="memory-image-container">
        <img 
          src={miraMemoryImage} 
          alt={memoryData.imageAlt}
          className="memory-image"
        />
      </div>
      
      <div className="memory-prompts">
        <h3 className="prompts-title">💭 Let's talk about this memory...</h3>
        <div className="prompts-grid">
          {memoryData.prompts.map((prompt, index) => (
            <button
              key={index}
              className="memory-prompt-btn"
              onClick={() => handlePromptClick(prompt)}
            >
              <span className="prompt-icon">🌸</span>
              <span className="prompt-text">{prompt}</span>
            </button>
          ))}
        </div>
      </div>
      
      <div className="memory-footer">
        <p className="memory-encouragement">
          💕 Take your time to remember this special moment with Mira
        </p>
      </div>
    </div>
  );
};

export default MemoryCapsule;