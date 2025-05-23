import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getDatabase } from 'firebase/database';
import { ref, onValue } from 'firebase/database';

// Type definitions for our mock implementations
interface MockAuth {
  currentUser: { uid: string; email: string } | null;
  onAuthStateChanged: (callback: (user: { uid: string; email: string } | null) => void) => () => void;
  signInWithEmailAndPassword: (email: string, password: string) => Promise<{ user: { uid: string; email: string } }>;
  createUserWithEmailAndPassword: (email: string, password: string) => Promise<{ user: { uid: string; email: string } }>;
  signOut: () => Promise<void>;
}

interface MockDatabase {
  ref: (path: string) => MockReference;
}

interface MockReference {
  set: (data: any) => Promise<void>;
  get: () => Promise<MockSnapshot>;
  push: () => MockReference & { key: string };
  update: (data: any) => Promise<void>;
  remove: () => Promise<void>;
  onValue: (callback: (snapshot: MockSnapshot) => void) => void;
  off: () => void;
}

interface MockSnapshot {
  exists: () => boolean;
  val: () => any;
}

// Firebase configuration
// In a production environment, these should be stored in environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "demo-key",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "eduguard-db.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "eduguard-db",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "eduguard-db.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "123456789",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:123456789:web:abcdef123456",
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL || "https://eduguard-db-default-rtdb.firebaseio.com"
};

// For development without Firebase credentials
let shouldUseMock = !import.meta.env.VITE_FIREBASE_API_KEY || import.meta.env.VITE_FIREBASE_API_KEY === "demo-key";

// In-memory storage for mock database
const mockStorage: Record<string, any> = {};

// Initialize Firebase or mock implementation
let app: any;
let auth: any;
let db: any;

if (!shouldUseMock) {
  try {
    // Real Firebase implementation
    console.log("Initializing Firebase with config:", JSON.stringify({
      ...firebaseConfig,
      apiKey: firebaseConfig.apiKey ? "API_KEY_PROVIDED" : "NO_API_KEY",
    }));
    
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    db = getDatabase(app);
    console.log("Firebase initialized successfully");
    
    // Test database connection
    const testDbRef = ref(db, '.info/connected');
    onValue(testDbRef, (snapshot) => {
      const connected = snapshot.val();
      console.log("Firebase Database connection state:", connected ? "connected" : "disconnected");
    });
    
  } catch (error) {
    console.error("Error initializing Firebase:", error);
    shouldUseMock = true;
  }
}

// Use mock implementation if Firebase init failed or we're in development mode
if (shouldUseMock) {
  console.log("Using mock Firebase implementation for development");
  
  // Mock app
  app = { name: "mock-app" };
  
  // Mock auth
  auth = {
    currentUser: null,
    onAuthStateChanged: (callback: (user: { uid: string; email: string } | null) => void) => {
      setTimeout(() => callback({ uid: 'mock-uid', email: 'user@example.com' }), 100);
      return () => {};
    },
    signInWithEmailAndPassword: async () => ({ user: { uid: 'mock-uid', email: 'user@example.com' } }),
    createUserWithEmailAndPassword: async () => ({ user: { uid: 'mock-uid', email: 'user@example.com' } }),
    signOut: async () => {}
  } as MockAuth;
  
  // Helper for mock database
  const createMockReference = (path: string): MockReference => {
    return {
      set: async (data) => {
        mockStorage[path] = data;
      },
      get: async () => ({
        exists: () => path in mockStorage,
        val: () => mockStorage[path] || {}
      }),
      push: () => {
        const key = 'mock-key-' + Math.random().toString(36).substring(2, 10);
        const newPath = path ? `${path}/${key}` : key;
        const ref = createMockReference(newPath);
        return Object.assign(ref, { key });
      },
      update: async (data) => {
        mockStorage[path] = { ...(mockStorage[path] || {}), ...data };
      },
      remove: async () => {
        delete mockStorage[path];
      },
      onValue: (callback) => {
        callback({
          exists: () => path in mockStorage,
          val: () => mockStorage[path] || {}
        });
      },
      off: () => {}
    };
  };
  
  // Mock database
  db = {
    ref: (path: string) => createMockReference(path)
  } as MockDatabase;
}

export { app, auth, db };
export default app; 