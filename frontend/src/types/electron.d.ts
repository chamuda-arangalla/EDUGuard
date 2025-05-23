/**
 * Type declarations for Electron APIs exposed through the preload script
 */
interface ElectronAPI {
  sendMessage: (channel: string, data: any) => void;
  on: (channel: string, callback: Function) => Function;
  invoke: (channel: string, data: any) => Promise<any>;
  
  // Monitoring methods
  startMonitoring: () => Promise<any>;
  stopMonitoring: () => Promise<any>;
  
  // Script runner methods
  runScript1: () => Promise<any>;
  runScript2: () => Promise<any>;
  runScript3: () => Promise<any>;
  runScript4: () => Promise<any>;
}

interface Env {
  nodeEnv: string;
}

interface Window {
  electron: ElectronAPI;
  env: Env;
} 