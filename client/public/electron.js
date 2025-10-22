const { app, BrowserWindow, Menu, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const { spawn } = require('child_process');

// Keep a global reference of the window object
let mainWindow;
let serverProcess;

// Start the Express server
function startServer() {
  // Don't start server if it's already running
  const serverPath = path.join(__dirname, '..', '..', 'server', 'index.js');
  
  // Check if server is already running
  const testConnection = require('http').get('http://localhost:5001/api/health', (res) => {
    console.log('Server already running');
  });
  
  testConnection.on('error', (err) => {
    console.log('Starting server...');
    serverProcess = spawn('node', [serverPath], {
      cwd: path.join(__dirname, '..', '..', 'server'),
      stdio: isDev ? 'inherit' : 'ignore'
    });

    serverProcess.on('error', (err) => {
      console.error('Failed to start server:', err);
    });
  });

  return new Promise((resolve) => {
    setTimeout(resolve, 3000); // Give server time to start
  });
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: false,
      allowRunningInsecureContent: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'icon.png'), // Add icon if available
    title: 'Chat Helper - Dementia Companion',
    show: false, // Don't show until ready-to-show
    titleBarStyle: 'default',
    backgroundColor: '#f8f9fa'
  });

  // Load the app - always use the built version for now
  const startUrl = `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Focus on the window for better accessibility
    mainWindow.focus();
  });

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Prevent navigation away from the app
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url !== mainWindow.webContents.getURL()) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });
}

// Create application menu
function createMenu() {
  const template = [
    {
      label: 'Chat Helper',
      submenu: [
        {
          label: 'About Chat Helper',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About Chat Helper',
              message: 'Chat Helper - Dementia Companion',
              detail: 'A compassionate chat interface designed for people with dementia.\\nFeatures voice input, memory conversations, and music integration.'
            });
          }
        },
        { type: 'separator' },
        {
          label: 'Preferences...',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            // Could open a preferences window
            console.log('Preferences clicked');
          }
        },
        { type: 'separator' },
        {
          label: 'Quit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        {
          label: 'Reload',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            mainWindow.reload();
          }
        },
        {
          label: 'Force Reload',
          accelerator: 'CmdOrCtrl+Shift+R',
          click: () => {
            mainWindow.webContents.reloadIgnoringCache();
          }
        },
        {
          label: 'Toggle Developer Tools',
          accelerator: 'F12',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        },
        { type: 'separator' },
        {
          label: 'Actual Size',
          accelerator: 'CmdOrCtrl+0',
          click: () => {
            mainWindow.webContents.setZoomLevel(0);
          }
        },
        {
          label: 'Zoom In',
          accelerator: 'CmdOrCtrl+Plus',
          click: () => {
            const currentZoom = mainWindow.webContents.getZoomLevel();
            mainWindow.webContents.setZoomLevel(currentZoom + 0.5);
          }
        },
        {
          label: 'Zoom Out',
          accelerator: 'CmdOrCtrl+-',
          click: () => {
            const currentZoom = mainWindow.webContents.getZoomLevel();
            mainWindow.webContents.setZoomLevel(currentZoom - 0.5);
          }
        },
        { type: 'separator' },
        {
          label: 'Toggle Fullscreen',
          accelerator: 'F11',
          click: () => {
            mainWindow.setFullScreen(!mainWindow.isFullScreen());
          }
        }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Voice Commands',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Voice Commands Help',
              message: 'Using Voice Input',
              detail: '1. Click the red microphone button\\n2. Speak clearly and naturally\\n3. Wait for the text to appear\\n4. Click send or press Enter\\n\\nTips:\\n• Speak in a quiet environment\\n• Keep sentences short and simple\\n• Allow microphone permissions when prompted'
            });
          }
        },
        {
          label: 'Keyboard Shortcuts',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Keyboard Shortcuts',
              message: 'Helpful Shortcuts',
              detail: 'Enter: Send message\\nCtrl/Cmd + R: Reload\\nF11: Fullscreen\\nCtrl/Cmd + Plus/Minus: Zoom\\nCtrl/Cmd + 0: Reset zoom\\nF12: Developer tools'
            });
          }
        },
        { type: 'separator' },
        {
          label: 'Learn More',
          click: () => {
            shell.openExternal('https://github.com');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// App event handlers
app.whenReady().then(async () => {
  console.log('Starting Chat Helper desktop application...');
  
  // Start the backend server first
  try {
    await startServer();
    console.log('Backend server started');
  } catch (error) {
    console.error('Error starting server:', error);
  }
  
  // Create the main window
  createWindow();
  
  // Create the application menu
  createMenu();
  
  // macOS specific: Re-create window when dock icon is clicked
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  // On macOS, keep app running even when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Clean up server process when app is quitting
app.on('before-quit', () => {
  if (serverProcess) {
    serverProcess.kill();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (event, contents) => {
  contents.on('new-window', (event, navigationUrl) => {
    event.preventDefault();
    shell.openExternal(navigationUrl);
  });
});

// IPC handlers for renderer process communication
ipcMain.handle('app-version', () => {
  return app.getVersion();
});

ipcMain.handle('show-message-box', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

// Handle voice recognition requests (future enhancement)
ipcMain.handle('start-speech-recognition', async () => {
  // This could integrate with native speech recognition APIs
  return { supported: true };
});

console.log('Electron main process loaded');