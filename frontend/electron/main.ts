import { app, BrowserWindow, ipcMain, shell, Notification } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Get proper __dirname in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const isDev = !app.isPackaged;
let mainWindow: BrowserWindow | null = null;

function createWindow() {
  // Don't create multiple windows
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    // Show window only when ready
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true
    },
    // Add app icon
    icon: path.join(__dirname, '../public/logo.png')
  });

  // Wait until the window is ready before showing it
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // In development, load from Vite dev server
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    // Open DevTools only in development
    mainWindow.webContents.openDevTools();
  } else {
    // In production, load the built files
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Open external links in browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// This method will be called when Electron has finished initialization
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Function to show system notifications
function showNotification(title: string, body: string) {
  if (Notification.isSupported()) {
    new Notification({
      title,
      body,
      icon: path.join(__dirname, '../public/logo.png')
    }).show();
  }
}

// IPC handlers for communication with Python backend
ipcMain.handle('start-monitoring', async () => {
  console.log('Received request to start monitoring');
  showNotification('EDUGuard Monitoring', 'Monitoring has started');
  return { success: true, message: 'Monitoring started via Electron' };
});

ipcMain.handle('stop-monitoring', async () => {
  console.log('Received request to stop monitoring');
  showNotification('EDUGuard Monitoring', 'Monitoring has stopped');
  return { success: true, message: 'Monitoring stopped via Electron' };
});

// Handlers for different backend scripts
ipcMain.handle('run-script-1', async () => {
  console.log('Running Posture Checking Script');
  showNotification('EDUGuard Posture Monitor', 'Posture monitoring activated. You will be alerted when poor posture is detected.');
  return { success: true, message: 'Posture checking activated' };
});

ipcMain.handle('run-script-2', async () => {
  console.log('Running Stress Level Checking Script');
  showNotification('EDUGuard Stress Monitor', 'Stress level monitoring activated. Remember to take deep breaths when prompted.');
  return { success: true, message: 'Stress level checking activated' };
});

ipcMain.handle('run-script-3', async () => {
  console.log('Running Eye Strain Checking Script');
  showNotification('EDUGuard Eye Care', 'Eye strain monitoring activated. Follow the 20-20-20 rule when prompted.');
  return { success: true, message: 'Eye strain checking activated' };
});

ipcMain.handle('run-script-4', async () => {
  console.log('Running Dehydration Checking Script');
  showNotification('EDUGuard Hydration', 'Hydration reminders activated. Stay hydrated for better focus and health.');
  return { success: true, message: 'Dehydration checking activated' };
}); 