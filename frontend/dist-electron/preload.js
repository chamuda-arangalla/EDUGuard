"use strict";
const electron = require("electron");
const electronAPI = {
  // Add methods that will be available to the renderer process
  sendMessage: (channel, data) => {
    electron.ipcRenderer.send(channel, data);
  },
  on: (channel, callback) => {
    const subscription = (_event, ...args) => callback(...args);
    electron.ipcRenderer.on(channel, subscription);
    return () => {
      electron.ipcRenderer.removeListener(channel, subscription);
    };
  },
  invoke: (channel, data) => {
    return electron.ipcRenderer.invoke(channel, data);
  },
  // Monitoring methods
  startMonitoring: () => electron.ipcRenderer.invoke("start-monitoring", {}),
  stopMonitoring: () => electron.ipcRenderer.invoke("stop-monitoring", {}),
  // Script runner methods
  runScript1: () => electron.ipcRenderer.invoke("run-script-1", {}),
  runScript2: () => electron.ipcRenderer.invoke("run-script-2", {}),
  runScript3: () => electron.ipcRenderer.invoke("run-script-3", {}),
  runScript4: () => electron.ipcRenderer.invoke("run-script-4", {})
};
electron.contextBridge.exposeInMainWorld("electron", electronAPI);
electron.contextBridge.exposeInMainWorld("env", {
  nodeEnv: process.env.NODE_ENV
});
