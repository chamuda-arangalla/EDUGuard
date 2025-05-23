import { contextBridge, ipcRenderer } from 'electron';

/**
 * The preload script runs before the renderer process is loaded,
 * and has access to both node.js and electron APIs.
 * 
 * It exposes safe APIs from Electron to the renderer process.
 */

const electronAPI = {
  // Add methods that will be available to the renderer process
  sendMessage: (channel: string, data: any) => {
    ipcRenderer.send(channel, data);
  },
  
  on: (channel: string, callback: Function) => {
    const subscription = (_event: Electron.IpcRendererEvent, ...args: any[]) => 
      callback(...args);
    
    ipcRenderer.on(channel, subscription);
    
    return () => {
      ipcRenderer.removeListener(channel, subscription);
    };
  },
  
  invoke: (channel: string, data: any) => {
    return ipcRenderer.invoke(channel, data);
  },

  // Monitoring methods
  startMonitoring: () => ipcRenderer.invoke('start-monitoring', {}),
  stopMonitoring: () => ipcRenderer.invoke('stop-monitoring', {}),
  
  // Script runner methods
  runScript1: () => ipcRenderer.invoke('run-script-1', {}),
  runScript2: () => ipcRenderer.invoke('run-script-2', {}),
  runScript3: () => ipcRenderer.invoke('run-script-3', {}),
  runScript4: () => ipcRenderer.invoke('run-script-4', {})
};

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', electronAPI);

// Expose additional node.js APIs or environment variables if needed
contextBridge.exposeInMainWorld('env', {
  nodeEnv: process.env.NODE_ENV
}); 