"use strict";
const electron = require("electron");
const path = require("node:path");
const node_url = require("node:url");
var _documentCurrentScript = typeof document !== "undefined" ? document.currentScript : null;
const __filename$1 = node_url.fileURLToPath(typeof document === "undefined" ? require("url").pathToFileURL(__filename).href : _documentCurrentScript && _documentCurrentScript.tagName.toUpperCase() === "SCRIPT" && _documentCurrentScript.src || new URL("main.js", document.baseURI).href);
const __dirname$1 = path.dirname(__filename$1);
const isDev = !electron.app.isPackaged;
let mainWindow = null;
function createWindow() {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
    return;
  }
  mainWindow = new electron.BrowserWindow({
    width: 1200,
    height: 800,
    // Show window only when ready
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname$1, "preload.js"),
      sandbox: true
    },
    // Add app icon
    icon: path.join(__dirname$1, "../public/logo.png")
  });
  mainWindow.once("ready-to-show", () => {
    mainWindow == null ? void 0 : mainWindow.show();
  });
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
  if (isDev) {
    mainWindow.loadURL("http://localhost:5173");
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname$1, "../dist/index.html"));
  }
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    electron.shell.openExternal(url);
    return { action: "deny" };
  });
}
electron.app.whenReady().then(() => {
  createWindow();
  electron.app.on("activate", () => {
    if (electron.BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});
electron.app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    electron.app.quit();
  }
});
function showNotification(title, body) {
  if (electron.Notification.isSupported()) {
    new electron.Notification({
      title,
      body,
      icon: path.join(__dirname$1, "../public/logo.png")
    }).show();
  }
}
electron.ipcMain.handle("start-monitoring", async () => {
  console.log("Received request to start monitoring");
  showNotification("EDUGuard Monitoring", "Monitoring has started");
  return { success: true, message: "Monitoring started via Electron" };
});
electron.ipcMain.handle("stop-monitoring", async () => {
  console.log("Received request to stop monitoring");
  showNotification("EDUGuard Monitoring", "Monitoring has stopped");
  return { success: true, message: "Monitoring stopped via Electron" };
});
electron.ipcMain.handle("run-script-1", async () => {
  console.log("Running Posture Checking Script");
  showNotification("EDUGuard Posture Monitor", "Posture monitoring activated. You will be alerted when poor posture is detected.");
  return { success: true, message: "Posture checking activated" };
});
electron.ipcMain.handle("run-script-2", async () => {
  console.log("Running Stress Level Checking Script");
  showNotification("EDUGuard Stress Monitor", "Stress level monitoring activated. Remember to take deep breaths when prompted.");
  return { success: true, message: "Stress level checking activated" };
});
electron.ipcMain.handle("run-script-3", async () => {
  console.log("Running Eye Strain Checking Script");
  showNotification("EDUGuard Eye Care", "Eye strain monitoring activated. Follow the 20-20-20 rule when prompted.");
  return { success: true, message: "Eye strain checking activated" };
});
electron.ipcMain.handle("run-script-4", async () => {
  console.log("Running Dehydration Checking Script");
  showNotification("EDUGuard Hydration", "Hydration reminders activated. Stay hydrated for better focus and health.");
  return { success: true, message: "Dehydration checking activated" };
});
