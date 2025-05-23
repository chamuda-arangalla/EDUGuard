import axios from 'axios';

// Define base URL for API calls
const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Increase timeout for slow connections
  timeout: 10000,
});

// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    
    // Return a default response structure to prevent UI breaking
    if (error.response && error.response.config && error.response.config.url) {
      // Handle user profile errors
      if (error.response.config.url.includes('/user/profile')) {
        const uid = error.response.config.url.split('uid=')[1];
        return {
          data: {
            status: 'success',
            user: {
              uid: uid || 'unknown',
              email: 'user@example.com',
              displayName: 'User',
              isOfflineData: true
            }
          }
        };
      }
      
      // Handle login/registration errors
      if (error.response.config.url.includes('/login') || 
          error.response.config.url.includes('/register')) {
        // Let authentication errors pass through to be handled by the auth context
        throw error;
      }
    }
    
    return Promise.reject(error);
  }
);

// Authentication endpoints
export const authService = {
  login: async (email: string, password: string) => {
    try {
      const response = await api.post('/login', { email, password });
      return response.data;
    } catch (error: any) {
      console.error('Login error:', error.response?.data || error.message);
      
      // Transform backend error messages to be more user-friendly
      if (error.response?.data?.message === 'Invalid credentials') {
        throw new Error('Incorrect email or password. Please try again.');
      }
      
      throw error;
    }
  },
  
  register: async (email: string, password: string, displayName?: string) => {
    try {
      const response = await api.post('/register', { email, password, displayName });
      return response.data;
    } catch (error: any) {
      console.error('Registration error:', error.response?.data || error.message);
      
      // Transform backend error messages to be more user-friendly
      if (error.response?.data?.message?.includes('already exists')) {
        throw new Error('Email already in use. Please try logging in or use a different email.');
      }
      
      throw error;
    }
  },

  getProfile: async (uid: string) => {
    try {
      const response = await api.get(`/user/profile?uid=${uid}`);
      return response.data;
    } catch (error: any) {
      console.error('Get profile error:', error.response?.data || error.message);
      
      // Return a minimal profile if we can't fetch from backend
      return {
        status: 'success',
        user: {
          uid: uid,
          email: 'user@example.com',
          displayName: `User-${uid.substring(0, 6)}`,
          isOfflineData: true
        }
      };
    }
  },
};

// Monitoring endpoints
export const monitoringService = {
  startMonitoring: async () => {
    try {
      const response = await api.post('/start-monitoring');
      return response.data;
    } catch (error: any) {
      console.error('Start monitoring error:', error.response?.data || error.message);
      // Return a default response to prevent UI errors
      return { status: 'error', message: 'Could not connect to monitoring service.' };
    }
  },
  
  stopMonitoring: async () => {
    try {
      const response = await api.post('/stop-monitoring');
      return response.data;
    } catch (error: any) {
      console.error('Stop monitoring error:', error.response?.data || error.message);
      // Return a default response to prevent UI errors
      return { status: 'error', message: 'Could not connect to monitoring service.' };
    }
  },
};

export default api; 