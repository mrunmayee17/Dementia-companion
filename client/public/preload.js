const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  
  showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
  
  startSpeechRecognition: () => ipcRenderer.invoke('start-speech-recognition'),
  
  // Platform information
  platform: process.platform,
  
  // Version info
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

// Log that preload script has loaded
console.log('Electron preload script loaded');