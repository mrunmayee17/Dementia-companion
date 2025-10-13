// Voice service for handling speech recognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export class VoiceService {
  private recognition: any = null;
  private isListening = false;

  constructor() {
    console.log('Initializing VoiceService...');
    // Check if browser supports speech recognition
    const SpeechRecognition = 
      (window as any).SpeechRecognition || 
      (window as any).webkitSpeechRecognition;

    console.log('SpeechRecognition support:', !!SpeechRecognition);
    
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.setupRecognition();
      console.log('Voice recognition initialized successfully');
    } else {
      console.warn('Speech recognition not supported in this environment');
    }
  }

  private setupRecognition() {
    if (!this.recognition) return;

    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
    
    // Set maximum alternatives for better accuracy
    this.recognition.maxAlternatives = 1;
  }

  public isSupported(): boolean {
    return this.recognition !== null;
  }

  public async startListening(): Promise<string> {
    return new Promise((resolve, reject) => {
      console.log('Starting speech recognition...');
      
      if (!this.recognition) {
        console.error('Speech recognition not supported');
        reject(new Error('Speech recognition not supported'));
        return;
      }

      if (this.isListening) {
        console.warn('Already listening');
        reject(new Error('Already listening'));
        return;
      }

      this.recognition.onresult = (event: any) => {
        console.log('Speech recognition result received');
        const result = event.results[0][0].transcript;
        console.log('Recognized text:', result);
        this.isListening = false;
        resolve(result);
      };

      this.recognition.onerror = (event: any) => {
        this.isListening = false;
        let errorMessage = 'Speech recognition error';
        
        switch (event.error) {
          case 'no-speech':
            errorMessage = 'No speech was detected. Please try again.';
            break;
          case 'audio-capture':
            errorMessage = 'No microphone was found. Please check your microphone connection.';
            break;
          case 'not-allowed':
            errorMessage = 'Microphone permission was denied. Please allow microphone access and try again.';
            break;
          case 'network':
            errorMessage = 'Network error occurred. Please check your internet connection.';
            break;
          default:
            errorMessage = `Speech recognition error: ${event.error}`;
        }
        
        reject(new Error(errorMessage));
      };

      this.recognition.onend = () => {
        this.isListening = false;
      };

      try {
        this.recognition.start();
        this.isListening = true;
      } catch (error) {
        this.isListening = false;
        reject(new Error('Failed to start speech recognition'));
      }
    });
  }

  public stopListening(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }

  public getIsListening(): boolean {
    return this.isListening;
  }
}

export const voiceService = new VoiceService();