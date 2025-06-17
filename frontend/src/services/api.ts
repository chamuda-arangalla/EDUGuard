/**
 * API Service
 * 
 * Provides centralized API communication for the EDUGuard application
 * with error handling and authentication management.
 */
import axios from 'axios';

// -----------------------------------------------------------------------------
// Configuration
// -----------------------------------------------------------------------------
const API_BASE_URL = 'http://localhost:5000/api';

// Default timeout (20 seconds)
const DEFAULT_TIMEOUT = 20000;

// Extended timeout for long-running operations (120 seconds)
const EXTENDED_TIMEOUT = 120000;

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: DEFAULT_TIMEOUT,
});

// -----------------------------------------------------------------------------
// Request Interceptors
// -----------------------------------------------------------------------------
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
    
    // Apply extended timeout for specific endpoints that may take longer
    if (config.url) {
      // Hydration monitoring endpoints need more time
      if (config.url.includes('/hydration/start') || 
          config.url.includes('/hydration/stop') ||
          config.url.includes('/webcam/start') ||
          config.url.includes('/reports/')) {
        console.log(`Applying extended timeout (${EXTENDED_TIMEOUT}ms) for: ${config.url}`);
        config.timeout = EXTENDED_TIMEOUT;
      }
    }
    
    return config;
  },
  error => Promise.reject(error)
);

// -----------------------------------------------------------------------------
// Response Interceptors
// -----------------------------------------------------------------------------
api.interceptors.response.use(
  response => response,
  error => {
    // Detailed error logging
    if (error.code === 'ECONNABORTED') {
      console.error(`Request timeout: ${error.config?.url} exceeded ${error.config?.timeout}ms`);
    } else {
      console.error('API Error:', error.message);
    }
    
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
      
      // For hydration monitoring errors, provide more helpful message
      if (error.response?.config?.url?.includes('/hydration/start')) {
        console.error('Hydration monitoring failed to start. This might be due to webcam server issues.');
        return {
          data: {
            status: 'error',
            message: 'Hydration monitoring failed to start. Please try again or restart the application.',
            monitoring: false
          }
        };
      }
    }
    
    return Promise.reject(error);
  }
);

// -----------------------------------------------------------------------------
// Authentication Services
// -----------------------------------------------------------------------------
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

// -----------------------------------------------------------------------------
// Generic Monitoring Services
// -----------------------------------------------------------------------------
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

// -----------------------------------------------------------------------------
// Posture Monitoring Services
// -----------------------------------------------------------------------------
export const postureService = {
  startMonitoring: async (progressReportId?: string) => {
    try {
      const payload = progressReportId ? { progressReportId } : {};
      const response = await api.post('/posture/start', payload);
      return response.data;
    } catch (error: any) {
      console.error('Start posture monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start posture monitoring.' 
      };
    }
  },
  
  stopMonitoring: async () => {
    try {
      const response = await api.post('/posture/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop posture monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop posture monitoring.' 
      };
    }
  },
  
  getStatus: async () => {
    try {
      const response = await api.get('/posture/status');
      return response.data;
    } catch (error: any) {
      console.error('Get posture status error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { is_monitoring: false, webcam_server_active: false } 
      };
    }
  },
  
  startWebcamServer: async () => {
    try {
      const response = await api.post('/posture/webcam/start');
      return response.data;
    } catch (error: any) {
      console.error('Start webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start webcam server.' 
      };
    }
  },
  
  stopWebcamServer: async () => {
    try {
      const response = await api.post('/posture/webcam/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop webcam server.' 
      };
    }
  },
  
  getRecentData: async (minutes = 5, includeAverage = true) => {
    try {
      const response = await api.get(
        `/posture/data/recent?minutes=${minutes}&includeAverage=${includeAverage}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Get posture data error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { predictions: [], average: null, minutes, user_id: null } 
      };
    }
  },
  
  getRecentAlerts: async (limit = 20) => {
    try {
      const response = await api.get(`/posture/alerts/recent?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      console.error('Get posture alerts error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { alerts: [], total_count: 0 } 
      };
    }
  },
  
  triggerAlertCheck: async () => {
    try {
      const response = await api.post('/posture/check-alerts');
      return response.data;
    } catch (error: any) {
      console.error('Trigger alert check error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not trigger alert check.' 
      };
    }
  }
};

// -----------------------------------------------------------------------------
// Stress Monitoring Services
// -----------------------------------------------------------------------------
export const stressService = {
  startMonitoring: async (progressReportId?: string) => {
    try {
      const payload = progressReportId ? { progressReportId } : {};
      const response = await api.post('/stress/start', payload);
      return response.data;
    } catch (error: any) {
      console.error('Start stress monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start stress monitoring.' 
      };
    }
  },
  
  stopMonitoring: async () => {
    try {
      const response = await api.post('/stress/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop stress monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop stress monitoring.' 
      };
    }
  },
  
  getStatus: async () => {
    try {
      const response = await api.get('/stress/status');
      return response.data;
    } catch (error: any) {
      console.error('Get stress status error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { is_monitoring: false, webcam_server_active: false } 
      };
    }
  },
  
  startWebcamServer: async () => {
    try {
      const response = await api.post('/stress/webcam/start');
      return response.data;
    } catch (error: any) {
      console.error('Start webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start webcam server.' 
      };
    }
  },
  
  stopWebcamServer: async () => {
    try {
      const response = await api.post('/stress/webcam/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop webcam server.' 
      };
    }
  },
  
  getRecentData: async (minutes = 5, includeAverage = true) => {
    try {
      const response = await api.get(
        `/stress/data/recent?minutes=${minutes}&includeAverage=${includeAverage}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Get stress data error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { predictions: [], average: null, minutes, user_id: null } 
      };
    }
  },
  
  getRecentAlerts: async (limit = 20) => {
    try {
      const response = await api.get(`/stress/alerts/recent?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      console.error('Get stress alerts error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { alerts: [], total_count: 0 } 
      };
    }
  },
  
  triggerAlertCheck: async () => {
    try {
      const response = await api.post('/stress/check-alerts');
      return response.data;
    } catch (error: any) {
      console.error('Trigger alert check error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not trigger alert check.' 
      };
    }
  }
};

// -----------------------------------------------------------------------------
// CVS Monitoring Services (Eye Blink Detection)
// -----------------------------------------------------------------------------
export const cvsService = {
  startMonitoring: async (progressReportId?: string) => {
    try {
      const payload = progressReportId ? { progressReportId } : {};
      const response = await api.post('/cvs/start', payload);
      return response.data;
    } catch (error: any) {
      console.error('Start CVS monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start CVS monitoring.' 
      };
    }
  },
  
  stopMonitoring: async () => {
    try {
      const response = await api.post('/cvs/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop CVS monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop CVS monitoring.' 
      };
    }
  },
  
  getStatus: async () => {
    try {
      const response = await api.get('/cvs/status');
      return response.data;
    } catch (error: any) {
      console.error('Get CVS status error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { is_monitoring: false, webcam_server_active: false } 
      };
    }
  },
  
  startWebcamServer: async () => {
    try {
      const response = await api.post('/cvs/webcam/start');
      return response.data;
    } catch (error: any) {
      console.error('Start webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start webcam server.' 
      };
    }
  },
  
  stopWebcamServer: async () => {
    try {
      const response = await api.post('/cvs/webcam/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop webcam server.' 
      };
    }
  },
  
  getRecentData: async (minutes = 5, includeAverage = true) => {
    try {
      const response = await api.get(
        `/cvs/data/recent?minutes=${minutes}&includeAverage=${includeAverage}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Get CVS data error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { predictions: [], average: null, minutes, user_id: null } 
      };
    }
  },
  
  getRecentAlerts: async (limit = 20) => {
    try {
      const response = await api.get(`/cvs/alerts/recent?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      console.error('Get CVS alerts error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { alerts: [], total_count: 0 } 
      };
    }
  },
  
  triggerAlertCheck: async () => {
    try {
      const response = await api.post('/cvs/check-alerts');
      return response.data;
    } catch (error: any) {
      console.error('Trigger alert check error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not trigger alert check.' 
      };
    }
  }
};

// -----------------------------------------------------------------------------
// Hydration Monitoring Services (Lip Dryness Detection)
// -----------------------------------------------------------------------------
export const hydrationService = {
  startMonitoring: async (progressReportId?: string) => {
    try {
      const payload = progressReportId ? { progressReportId } : {};
      const response = await api.post('/hydration/start', payload);
      return response.data;
    } catch (error: any) {
      console.error('Start hydration monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start hydration monitoring.' 
      };
    }
  },
  
  stopMonitoring: async () => {
    try {
      const response = await api.post('/hydration/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop hydration monitoring error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop hydration monitoring.' 
      };
    }
  },
  
  getStatus: async () => {
    try {
      const response = await api.get('/hydration/status');
      return response.data;
    } catch (error: any) {
      console.error('Get hydration status error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { is_monitoring: false, webcam_server_active: false } 
      };
    }
  },
  
  startWebcamServer: async () => {
    try {
      const response = await api.post('/hydration/webcam/start');
      return response.data;
    } catch (error: any) {
      console.error('Start webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not start webcam server.' 
      };
    }
  },
  
  stopWebcamServer: async () => {
    try {
      const response = await api.post('/hydration/webcam/stop');
      return response.data;
    } catch (error: any) {
      console.error('Stop webcam server error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not stop webcam server.' 
      };
    }
  },
  
  getRecentData: async (minutes = 5, includeAverage = true) => {
    try {
      const response = await api.get(
        `/hydration/data/recent?minutes=${minutes}&includeAverage=${includeAverage}`
      );
      return response.data;
    } catch (error: any) {
      console.error('Get hydration data error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { predictions: [], average: null, minutes, user_id: null } 
      };
    }
  },
  
  getRecentAlerts: async (limit = 20) => {
    try {
      const response = await api.get(`/hydration/alerts/recent?limit=${limit}`);
      return response.data;
    } catch (error: any) {
      console.error('Get hydration alerts error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        data: { alerts: [], total_count: 0 } 
      };
    }
  },
  
  triggerAlertCheck: async () => {
    try {
      const response = await api.post('/hydration/check-alerts');
      return response.data;
    } catch (error: any) {
      console.error('Trigger alert check error:', error.response?.data || error.message);
      return { 
        status: 'error', 
        message: error.response?.data?.message || 'Could not trigger alert check.' 
      };
    }
  }
};

// -----------------------------------------------------------------------------
// Reports Services
// -----------------------------------------------------------------------------
export const reportsService = {
  // Get historical posture data with filtering
  getPostureHistory: async (timeframe: 'daily' | 'weekly' | 'monthly', date?: string) => {
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        console.error('No user ID found in local storage for posture history request');
        return {
          status: 'error',
          message: 'User ID is required to fetch data',
          data: null
        };
      }
      
      const params = date ? `&date=${date}` : '';
      const url = `/reports/posture?timeframe=${timeframe}${params}&userId=${userId}`;
      console.log(`Fetching posture history: ${url}`);
      
      // Use extended timeout for report endpoints
      const response = await api.get(url, { timeout: 60000 });
      return response.data;
    } catch (error: any) {
      console.error('Get posture history error:', error.response?.data || error.message);
      return {
        status: 'error',
        message: 'Failed to load posture history data',
        data: null
      };
    }
  },
  
  // Get historical stress data with filtering
  getStressHistory: async (timeframe: 'daily' | 'weekly' | 'monthly', date?: string) => {
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        console.error('No user ID found in local storage for stress history request');
        return {
          status: 'error',
          message: 'User ID is required to fetch data',
          data: null
        };
      }
      
      const params = date ? `&date=${date}` : '';
      const url = `/reports/stress?timeframe=${timeframe}${params}&userId=${userId}`;
      console.log(`Fetching stress history: ${url}`);
      
      // Use extended timeout for report endpoints
      const response = await api.get(url, { timeout: 60000 });
      return response.data;
    } catch (error: any) {
      console.error('Get stress history error:', error.response?.data || error.message);
      return {
        status: 'error',
        message: 'Failed to load stress history data',
        data: null
      };
    }
  },
  
  // Get historical CVS (eye strain) data with filtering
  getCVSHistory: async (timeframe: 'daily' | 'weekly' | 'monthly', date?: string) => {
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        console.error('No user ID found in local storage for CVS history request');
        return {
          status: 'error',
          message: 'User ID is required to fetch data',
          data: null
        };
      }
      
      const params = date ? `&date=${date}` : '';
      const url = `/reports/cvs?timeframe=${timeframe}${params}&userId=${userId}`;
      console.log(`Fetching CVS history: ${url}`);
      
      // Use extended timeout for report endpoints
      const response = await api.get(url, { timeout: 60000 });
      return response.data;
    } catch (error: any) {
      console.error('Get CVS history error:', error.response?.data || error.message);
      return {
        status: 'error',
        message: 'Failed to load eye strain history data',
        data: null
      };
    }
  },
  
  // Get historical hydration data with filtering
  getHydrationHistory: async (timeframe: 'daily' | 'weekly' | 'monthly', date?: string) => {
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        console.error('No user ID found in local storage for hydration history request');
        return {
          status: 'error',
          message: 'User ID is required to fetch data',
          data: null
        };
      }
      
      const params = date ? `&date=${date}` : '';
      const url = `/reports/hydration?timeframe=${timeframe}${params}&userId=${userId}`;
      console.log(`Fetching hydration history: ${url}`);
      
      // Use extended timeout for report endpoints (2 minutes)
      const response = await api.get(url, { timeout: 120000 });
      
      // Check if response data is empty or missing required fields
      if (!response.data.data || 
          !response.data.data.labels || 
          response.data.data.labels.length === 0 ||
          !response.data.data.normal_lips_percentage ||
          !response.data.data.dry_lips_percentage) {
        
        console.log('Empty or invalid hydration data received, using sample data');
        return {
          status: 'success',
          data: generateSampleHydrationData(timeframe),
          message: 'Sample hydration data provided'
        };
      }
      
      return response.data;
    } catch (error: any) {
      console.error('Get hydration history error:', error.response?.data || error.message);
      console.log('Providing sample hydration data due to API error');
      
      return {
        status: 'success',
        data: generateSampleHydrationData(timeframe),
        message: 'Sample hydration data provided due to API error',
        is_fallback_data: true
      };
    }
  },
  
  // Get summary data across all monitoring types
  getSummaryData: async (timeframe: 'daily' | 'weekly' | 'monthly') => {
    try {
      const userId = localStorage.getItem('userId');
      if (!userId) {
        console.error('No user ID found in local storage for summary data request');
        return {
          status: 'error',
          message: 'User ID is required to fetch data',
          data: null
        };
      }
      
      const url = `/reports/summary?timeframe=${timeframe}&userId=${userId}`;
      console.log(`Fetching summary data: ${url}`);
      
      // Use extended timeout for report endpoints (2 minutes)
      const response = await api.get(url, { timeout: 120000 });
      return response.data;
    } catch (error: any) {
      console.error('Get summary data error:', error);
      console.log('Request details:', error?.config);
      return {
        status: 'error',
        message: 'Failed to load summary data',
        data: null
      };
    }
  }
};

// Helper function to generate sample hydration data based on timeframe
const generateSampleHydrationData = (timeframe: 'daily' | 'weekly' | 'monthly') => {
  let labels: string[] = [];
  let dataPoints = 0;
  
  // Generate appropriate labels based on timeframe
  if (timeframe === 'daily') {
    labels = ['8 AM', '9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM'];
    dataPoints = labels.length;
  } else if (timeframe === 'weekly') {
    labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    dataPoints = labels.length;
  } else { // monthly
    labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
    dataPoints = labels.length;
  }
  
  // Generate sample data arrays
  const normalLipsPercentage = Array.from({ length: dataPoints }, () => 
    Math.floor(Math.random() * 40) + 50); // Random values between 50-90%
  
  const dryLipsPercentage = normalLipsPercentage.map(val => 100 - val);
  
  const avgDrynessScore = normalLipsPercentage.map(val => 
    parseFloat((1 - (val / 100) * 0.8).toFixed(2))); // Higher when lips are drier
  
  return {
    labels,
    normal_lips_percentage: normalLipsPercentage,
    dry_lips_percentage: dryLipsPercentage,
    avg_dryness_score: avgDrynessScore,
    is_sample_data: true
  };
};

export default api; 