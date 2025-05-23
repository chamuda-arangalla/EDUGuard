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

// Add request interceptor to add user ID to all requests
api.interceptors.request.use(
  config => {
    // Add user ID from local storage if available
    const userId = localStorage.getItem('userId');
    if (userId) {
      console.log(`Adding user ID ${userId} to request headers`);
      config.headers['X-User-ID'] = userId;
      
      // Also add as query parameter for endpoints that might need it
      if (config.url && !config.url.includes('?')) {
        config.url = `${config.url}?userId=${userId}`;
      } else if (config.url && !config.url.includes('userId=')) {
        config.url = `${config.url}&userId=${userId}`;
      }
    } else {
      console.warn('No user ID found in local storage for API request');
    }
    return config;
  },
  error => Promise.reject(error)
);

// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.message);
    console.error('Request details:', {
      url: error.config?.url,
      method: error.config?.method,
      headers: error.config?.headers
    });
    
    // Return a default response structure to prevent UI breaking
    if (error.response && error.response.config && error.response.config.url) {
      // Handle user profile errors
      if (error.response.config.url.includes('/user/profile')) {
        const uid = error.response.config.url.split('userId=')[1]?.split('&')[0] || 
                  localStorage.getItem('userId') || 'unknown';
        console.log(`Generating fallback profile for user ${uid}`);
        return {
          data: {
            status: 'success',
            profile: {
              uid: uid,
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
      if (response.data.status === 'success' && response.data.uid) {
        // Store user ID in local storage for future requests
        localStorage.setItem('userId', response.data.uid);
        console.log(`Stored user ID ${response.data.uid} in local storage after login`);
      }
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
      if (response.data.status === 'success' && response.data.uid) {
        // Store user ID in local storage for future requests
        localStorage.setItem('userId', response.data.uid);
        console.log(`Stored user ID ${response.data.uid} in local storage after registration`);
      }
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
      // Store the user ID for future requests
      localStorage.setItem('userId', uid);
      console.log(`Stored user ID ${uid} in local storage before profile fetch`);
      
      // Make sure to pass the user ID in both header and query param
      const response = await api.get(`/user/profile?userId=${uid}`);
      return response.data;
    } catch (error: any) {
      console.error('Get profile error:', error.response?.data || error.message);
      
      // Return a minimal profile if we can't fetch from backend
      return {
        status: 'success',
        profile: {
          uid: uid,
          email: 'user@example.com',
          displayName: `User-${uid.substring(0, 6)}`,
          isOfflineData: true
        }
      };
    }
  },
  
  updateProfile: async (profileData: any) => {
    try {
      // Make sure user ID is in local storage
      const userId = localStorage.getItem('userId');
      if (!userId) {
        console.error('Cannot update profile: No user ID in local storage');
        throw new Error('User ID not found');
      }
      
      const response = await api.put(`/user/profile?userId=${userId}`, profileData);
      return response.data;
    } catch (error: any) {
      console.error('Update profile error:', error.response?.data || error.message);
      throw error;
    }
  },
  
  logout: async () => {
    // Clear user ID from local storage
    console.log('Removing user ID from local storage during logout');
    localStorage.removeItem('userId');
  }
};

// Monitoring endpoints
export const monitoringService = {
  getStatus: async () => {
    try {
      const response = await api.get('/status');
      return response.data;
    } catch (error: any) {
      console.error('Get status error:', error.response?.data || error.message);
      return { running: false };
    }
  },
  
  startMonitoring: async () => {
    try {
      const response = await api.post('/start');
      return response.data;
    } catch (error: any) {
      console.error('Start monitoring error:', error.response?.data || error.message);
      // Return a default response to prevent UI errors
      return { status: 'error', message: 'Could not connect to monitoring service.' };
    }
  },
  
  stopMonitoring: async () => {
    try {
      const response = await api.post('/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop monitoring error:', error.response?.data || error.message);
      // Return a default response to prevent UI errors
      return { status: 'error', message: 'Could not connect to monitoring service.' };
    }
  },
  
  getRecentAlerts: async (limit = 20) => {
    try {
      const response = await api.get(`/alerts/recent?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      console.error('Get alerts error:', error.response?.data || error.message);
      return [];
    }
  },
  
  getRecentPredictions: async (model: string, minutes = 5, includeAverage = true) => {
    try {
      const response = await api.get(
        `/predictions/recent?model=${model}&minutes=${minutes}&includeAverage=${includeAverage}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Get predictions error:', error.response?.data || error.message);
      return { predictions: [], average: null, model, minutes };
    }
  }
};

export default api; 