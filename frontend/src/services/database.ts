// Type-safe database service for both real Firebase and mock implementation
// This avoids direct Firebase imports which can cause issues when using mock implementations

import { db } from '../config/firebase';
import { 
  ref, set, push, get, update, remove, onValue, off,
  DatabaseReference, DataSnapshot
} from 'firebase/database';

// Check if this is a mock database or real Firebase database
const isMockDatabase = (db: any): boolean => {
  return db && typeof db.ref === 'function';
};

// Define more specific types for database operations
type DBReference = {
  set: (data: any) => Promise<any>;
  get: () => Promise<{ exists: () => boolean; val: () => any }>;
  push: () => { key: string | null; set: (data: any) => Promise<any> };
  update: (data: any) => Promise<any>;
  remove: () => Promise<any>;
  onValue: (callback: (snapshot: { exists: () => boolean; val: () => any }) => void) => any;
  off: () => void;
};

type DB = {
  ref: (path: string) => DBReference;
};

// Helper function to get a reference based on database type
const getReference = (path: string): any => {
  if (isMockDatabase(db)) {
    // Use the mock database's ref method
    return (db as DB).ref(path);
  } else {
    // Use the Firebase v9 modular API
    return ref(db, path);
  }
};

// Create data
export const createData = async (path: string, data: any) => {
  try {
    const reference = getReference(path);
    
    if (isMockDatabase(db)) {
      await reference.set(data);
    } else {
      await set(reference, data);
    }
    
    return { success: true };
  } catch (error) {
    console.error('Error creating data:', error);
    return { success: false, error };
  }
};

// Create data with auto-generated ID
export const createDataWithId = async (path: string, data: any) => {
  try {
    if (isMockDatabase(db)) {
      const reference = (db as DB).ref(path);
      const newRef = reference.push();
      const id = newRef.key;
      await newRef.set(data);
      return { success: true, id };
    } else {
      const reference = ref(db, path);
      const newRef = push(reference);
      const id = newRef.key;
      await set(newRef, data);
      return { success: true, id };
    }
  } catch (error) {
    console.error('Error creating data with ID:', error);
    return { success: false, error };
  }
};

// Read data once
export const readData = async (path: string) => {
  try {
    const reference = getReference(path);
    
    let snapshot;
    if (isMockDatabase(db)) {
      snapshot = await reference.get();
    } else {
      snapshot = await get(reference);
    }
    
    if ((typeof snapshot.exists === 'function' && snapshot.exists()) || 
        (typeof snapshot.exists !== 'function' && snapshot.val() !== null)) {
      return { success: true, data: snapshot.val() };
    } else {
      return { success: true, data: null };
    }
  } catch (error) {
    console.error('Error reading data:', error);
    // Return empty data object instead of failing completely
    return { success: true, data: {} };
  }
};

// Subscribe to data changes
export const subscribeToData = (path: string, callback: (data: any) => void) => {
  try {
    const reference = getReference(path);
    
    if (isMockDatabase(db)) {
      reference.onValue((snapshot: any) => {
        try {
          const data = snapshot.val();
          callback(data);
        } catch (error) {
          console.error('Error processing snapshot:', error);
          callback(null);
        }
      });
      
      // Return unsubscribe function 
      return () => {
        try {
          reference.off();
        } catch (error) {
          console.error('Error unsubscribing:', error);
        }
      };
    } else {
      // Firebase v9 implementation
      const unsubscribe = onValue(reference, (snapshot) => {
        try {
          const data = snapshot.val();
          callback(data);
        } catch (error) {
          console.error('Error processing snapshot:', error);
          callback(null);
        }
      });
      
      // Return unsubscribe function
      return unsubscribe;
    }
  } catch (error) {
    console.error(`Error setting up subscription:`, error);
    // Return a dummy unsubscribe function
    callback(null);
    return () => {};
  }
};

// Update data
export const updateData = async (path: string, data: any) => {
  try {
    const reference = getReference(path);
    
    if (isMockDatabase(db)) {
      await reference.update(data);
    } else {
      await update(reference, data);
    }
    
    return { success: true };
  } catch (error) {
    console.error('Error updating data:', error);
    return { success: false, error };
  }
};

// Delete data
export const deleteData = async (path: string) => {
  try {
    const reference = getReference(path);
    
    if (isMockDatabase(db)) {
      await reference.remove();
    } else {
      await remove(reference);
    }
    
    return { success: true };
  } catch (error) {
    console.error('Error deleting data:', error);
    return { success: false, error };
  }
};

// Query data - simplified to work with mock implementation
export const queryData = async (path: string, child: string, value: string | number | boolean) => {
  try {
    // For the mock implementation, we'll just fetch all data
    const reference = getReference(path);
    
    let snapshot;
    if (isMockDatabase(db)) {
      snapshot = await reference.get();
    } else {
      snapshot = await get(reference);
    }
    
    const exists = typeof snapshot.exists === 'function' 
      ? snapshot.exists() 
      : snapshot.val() !== null;
      
    if (exists) {
      const data = snapshot.val();
      
      // Filter the data manually
      const filtered = Object.entries(data)
        .filter(([_, item]) => (item as any)[child] === value)
        .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});
      
      return { success: true, data: filtered };
    } else {
      return { success: true, data: null };
    }
  } catch (error) {
    console.error('Error querying data:', error);
    // Return empty data instead of failing
    return { success: true, data: {} };
  }
}; 