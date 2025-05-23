import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  User,
  AuthErrorCodes,
} from 'firebase/auth';
import { auth } from '../config/firebase';
import { authService } from '../services/api';

interface UserProfile {
  email: string;
  displayName?: string;
  createdAt?: string;
  lastLogin?: string;
  [key: string]: any; // For any additional profile fields
}

interface AuthContextType {
  user: User | null;
  userProfile: UserProfile | null;
  loading: boolean;
  profileLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState(0);

  const createMinimalProfile = (currentUser: User): UserProfile => {
    return {
      email: currentUser.email || '',
      displayName: currentUser.displayName || currentUser.email?.split('@')[0] || '',
      uid: currentUser.uid,
    };
  };

  const fetchUserProfile = useCallback(async (currentUser: User | null) => {
    if (!currentUser) {
      setUserProfile(null);
      return;
    }
    
    // Prevent fetching too frequently (no more than once per 5 seconds)
    const now = Date.now();
    if (now - lastFetchTime < 5000) {
      console.log('Skipping profile fetch - too recent');
      return;
    }
    
    try {
      setProfileLoading(true);
      setLastFetchTime(now);
      
      const response = await authService.getProfile(currentUser.uid);
      
      if (response.status === 'success' && response.user) {
        setUserProfile(response.user);
      } else {
        // If profile not found, create a minimal profile with Firebase data
        setUserProfile(createMinimalProfile(currentUser));
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      // Create a minimal profile with the data we have from Firebase
      setUserProfile(createMinimalProfile(currentUser));
    } finally {
      setProfileLoading(false);
    }
  }, [lastFetchTime]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      if (currentUser) {
        await fetchUserProfile(currentUser);
      } else {
        setUserProfile(null);
      }
      setLoading(false);
    });

    return unsubscribe;
  }, [fetchUserProfile]);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      // Authenticate with Firebase
      const firebaseResult = await signInWithEmailAndPassword(auth, email, password);
      
      // Then authenticate with backend to get the user profile
      try {
        const backendResponse = await authService.login(email, password);
        if (backendResponse.status === 'success' && backendResponse.user) {
          setUserProfile(backendResponse.user);
        } else {
          await fetchUserProfile(firebaseResult.user);
        }
      } catch (backendError) {
        console.error("Backend authentication failed:", backendError);
        // Still set the user from Firebase
        setUserProfile(createMinimalProfile(firebaseResult.user));
      }
    } catch (error: any) {
      console.error('Login error:', error);
      
      // Handle specific Firebase error messages
      if (error.code === AuthErrorCodes.USER_DELETED) {
        throw new Error('User not found. Please check your email and try again.');
      } else if (error.code === AuthErrorCodes.INVALID_PASSWORD) {
        throw new Error('Invalid password. Please try again.');
      } else {
        throw error;
      }
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, displayName?: string) => {
    try {
      setLoading(true);
      
      // Try backend registration first
      let backendSuccess = false;
      try {
        const backendResponse = await authService.register(email, password, displayName);
        if (backendResponse.status === 'success') {
          backendSuccess = true;
          
          // If backend registration succeeded, sign in with Firebase
          const firebaseResult = await signInWithEmailAndPassword(auth, email, password);
          setUser(firebaseResult.user);
          
          if (backendResponse.user) {
            setUserProfile(backendResponse.user);
          } else {
            setUserProfile(createMinimalProfile(firebaseResult.user));
          }
          
          return;
        }
      } catch (backendError) {
        console.error("Backend registration failed:", backendError);
        // Continue with Firebase registration
      }
      
      // If backend failed, try Firebase registration
      if (!backendSuccess) {
        try {
          const firebaseResult = await createUserWithEmailAndPassword(auth, email, password);
          setUser(firebaseResult.user);
          setUserProfile(createMinimalProfile(firebaseResult.user));
        } catch (firebaseError: any) {
          console.error('Firebase registration error:', firebaseError);
          
          // Handle specific Firebase error messages for registration
          if (firebaseError.code === AuthErrorCodes.EMAIL_EXISTS) {
            throw new Error('Email already in use. Try logging in instead.');
          } else if (firebaseError.code === AuthErrorCodes.WEAK_PASSWORD) {
            throw new Error('Password is too weak. Please use a stronger password.');
          } else {
            throw firebaseError;
          }
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      await signOut(auth);
      setUserProfile(null);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const refreshProfile = useCallback(async () => {
    if (!auth.currentUser) return;
    await fetchUserProfile(auth.currentUser);
  }, [fetchUserProfile]);

  const value = {
    user,
    userProfile,
    loading,
    profileLoading,
    login,
    register,
    logout,
    refreshProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}; 