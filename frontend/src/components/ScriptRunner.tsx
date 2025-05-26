/**
 * ScriptRunner Component
 * 
 * This component manages the health monitoring tools in the EDUGuard application,
 * including posture, stress, eye strain, and hydration monitoring.
 */
import React, { useState, useEffect } from 'react';

// Material UI Components
import { 
  Box, 
  Button, 
  Grid, 
  Typography, 
  Paper, 
  Snackbar, 
  Alert,
  CircularProgress,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Stack,
  IconButton,
  Collapse
} from '@mui/material';

// Material UI Icons
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import AccessibilityNewIcon from '@mui/icons-material/AccessibilityNew';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LocalDrinkIcon from '@mui/icons-material/LocalDrink';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';

// API Services
import { postureService, stressService, cvsService, hydrationService } from '../services/api';

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------
type ScriptColor = 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error';

interface Script {
  id: number;
  name: string;
  description: string;
  icon: React.ReactNode;
  method: () => Promise<any>;
  color: ScriptColor;
  isEnhanced?: boolean;
}

interface PostureData {
  predictions: any[];
  average: {
    good_posture_count: number;
    bad_posture_count: number;
    good_posture_percentage: number;
    bad_posture_percentage: number;
    total_samples: number;
  } | null;
  minutes: number;
}

interface StressData {
  predictions: any[];
  average: {
    low_stress_count: number;
    medium_stress_count: number;
    high_stress_count: number;
    low_stress_percentage: number;
    medium_stress_percentage: number;
    high_stress_percentage: number;
    total_samples: number;
  } | null;
  minutes: number;
}

interface CVSData {
  predictions: any[];
  average: {
    avg_blink_count: number;
    low_blink_count: number;
    normal_blink_count: number;
    high_blink_count: number;
    low_blink_percentage: number;
    normal_blink_percentage: number;
    high_blink_percentage: number;
    total_samples: number;
    samples?: number;
  } | null;
  minutes: number;
  user_id?: string | null;
}

interface HydrationData {
  predictions: any[];
  average: {
    dry_lips_count: number;
    normal_lips_count: number;
    dry_lips_percentage: number;
    normal_lips_percentage: number;
    avg_dryness_score: number;
    total_samples: number;
    samples?: number;
  } | null;
  minutes: number;
  user_id?: string | null;
}

interface PostureAlert {
  id: string;
  type: string;
  message: string;
  level: string;
  timestamp: number;
  created_at: string;
  read: boolean;
  data?: {
    bad_posture_percentage: number;
    total_samples: number;
    good_posture_count: number;
    bad_posture_count: number;
  };
}

interface StressAlert {
  id: string;
  type: string;
  message: string;
  level: string;
  timestamp: number;
  created_at: string;
  read: boolean;
  data?: {
    high_stress_percentage: number;
    total_samples: number;
    low_stress_count: number;
    medium_stress_count: number;
    high_stress_count: number;
  };
}

interface CVSAlert {
  id: string;
  type: string;
  message: string;
  level: string;
  timestamp: number;
  created_at: string;
  read: boolean;
  data?: {
    avg_blink_count: number;
    low_blink_percentage: number;
    high_blink_percentage: number;
    total_samples: number;
    threshold: number;
    alert_type: string;
  };
}

interface HydrationAlert {
  id: string;
  type: string;
  message: string;
  level: string;
  timestamp: number;
  created_at: string;
  read: boolean;
  data?: {
    dry_lips_percentage: number;
    normal_lips_percentage: number;
    total_samples: number;
    threshold: number;
  };
}

/**
 * ScriptRunner Component
 * 
 * Manages the health monitoring tools in the application
 */
const ScriptRunner: React.FC = () => {
  // -----------------------------------------------------------------------------
  // State Variables
  // -----------------------------------------------------------------------------
  // General state
  const [loading, setLoading] = useState<number | null>(null);
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error' | 'warning' | 'info'} | null>(null);
  const [webcamServerActive, setWebcamServerActive] = useState(false);
  const [webcamLoading, setWebcamLoading] = useState(false);
  
  // Posture monitoring state
  const [postureMonitoring, setPostureMonitoring] = useState(false);
  const [postureData, setPostureData] = useState<PostureData | null>(null);
  const [postureAlerts, setPostureAlerts] = useState<PostureAlert[]>([]);
  const [expandedPosture, setExpandedPosture] = useState(true);
  
  // Stress monitoring state
  const [stressMonitoring, setStressMonitoring] = useState(false);
  const [stressData, setStressData] = useState<StressData | null>(null);
  const [stressAlerts, setStressAlerts] = useState<StressAlert[]>([]);
  const [expandedStress, setExpandedStress] = useState(true);
  
  // CVS (eye strain) monitoring state
  const [cvsMonitoring, setCvsMonitoring] = useState(false);
  const [cvsData, setCvsData] = useState<CVSData | null>(null);
  const [cvsAlerts, setCvsAlerts] = useState<CVSAlert[]>([]);
  const [expandedCVS, setExpandedCVS] = useState(true);
  
  // Hydration monitoring state
  const [hydrationMonitoring, setHydrationMonitoring] = useState(false);
  const [hydrationData, setHydrationData] = useState<HydrationData | null>(null);
  const [hydrationAlerts, setHydrationAlerts] = useState<HydrationAlert[]>([]);
  const [expandedHydration, setExpandedHydration] = useState(true);
  
  // Polling intervals
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [stressPollingInterval, setStressPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [cvsPollingInterval, setCVSPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [hydrationPollingInterval, setHydrationPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // -----------------------------------------------------------------------------
  // Webcam Server Control Functions
  // -----------------------------------------------------------------------------
  const startWebcamServer = async () => {
    try {
      setWebcamLoading(true);
      const response = await postureService.startWebcamServer();
      if (response.status === 'success') {
        setWebcamServerActive(true);
        setNotification({
          message: 'Webcam server started successfully!',
          type: 'success'
        });
      } else {
        setNotification({
          message: response.message || 'Failed to start webcam server',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error starting webcam server. Please ensure the backend is running.',
        type: 'error'
      });
    } finally {
      setWebcamLoading(false);
    }
  };

  const stopWebcamServer = async () => {
    try {
      setWebcamLoading(true);
      const response = await postureService.stopWebcamServer();
      if (response.status === 'success') {
        setWebcamServerActive(false);
        setNotification({
          message: 'Webcam server stopped successfully!',
          type: 'success'
        });
      } else {
        setNotification({
          message: response.message || 'Failed to stop webcam server',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error stopping webcam server. The server might be in use by monitoring processes.',
        type: 'error'
      });
    } finally {
      setWebcamLoading(false);
    }
  };

  // -----------------------------------------------------------------------------
  // Posture Monitoring Functions
  // -----------------------------------------------------------------------------
  const startPostureMonitoring = async () => {
    try {
      // If webcam server is not active, try to start it first
      if (!webcamServerActive) {
        setNotification({
          message: 'Starting webcam server first...',
          type: 'info'
        });
        
        await startWebcamServer();
        // Small delay to ensure webcam server is fully started
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      const response = await postureService.startMonitoring();
      if (response.status === 'success') {
        setPostureMonitoring(true);
        setNotification({
          message: 'Enhanced posture monitoring started successfully!',
          type: 'success'
        });
        // Start polling for data
        startDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to start posture monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error starting posture monitoring. Please ensure the backend is running.',
        type: 'error'
      });
    }
  };

  const stopPostureMonitoring = async () => {
    try {
      const response = await postureService.stopMonitoring();
      if (response.status === 'success') {
        setPostureMonitoring(false);
        setNotification({
          message: 'Posture monitoring stopped successfully!',
          type: 'success'
        });
        // Stop polling
        stopDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to stop posture monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error stopping posture monitoring',
        type: 'error'
      });
    }
  };

  // Data polling for real-time posture updates
  const startDataPolling = () => {
    // Poll every 30 seconds for posture data
    const interval = setInterval(async () => {
      try {
        // Get recent posture data
        const dataResponse = await postureService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          setPostureData(dataResponse.data);
          
          // Check for new alerts
          const alertsResponse = await postureService.getRecentAlerts(10);
          if (alertsResponse.status === 'success') {
            const alerts = alertsResponse.data.alerts;
            setPostureAlerts(alerts);
            
            // Show notification for new alerts
            const recentAlert = alerts.find((alert: PostureAlert) => 
              !alert.read && new Date(alert.created_at).getTime() > Date.now() - 60000 // Last minute
            );
            
            if (recentAlert) {
              setNotification({
                message: recentAlert.message,
                type: 'warning'
              });
            }
          }
        }
      } catch (error) {
        console.error('Error polling posture data:', error);
      }
    }, 30000);
    
    setPollingInterval(interval);
    
    // Get initial data immediately
    setTimeout(async () => {
      try {
        const dataResponse = await postureService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          setPostureData(dataResponse.data);
        }
        const alertsResponse = await postureService.getRecentAlerts(10);
        if (alertsResponse.status === 'success') {
          setPostureAlerts(alertsResponse.data.alerts);
        }
      } catch (error) {
        console.error('Error getting initial posture data:', error);
      }
    }, 3000);
  };

  const stopDataPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
    setPostureData(null);
    setPostureAlerts([]);
  };

  // -----------------------------------------------------------------------------
  // Stress Monitoring Functions
  // -----------------------------------------------------------------------------
  const startStressMonitoring = async () => {
    try {
      // If webcam server is not active, try to start it first
      if (!webcamServerActive) {
        setNotification({
          message: 'Starting webcam server first...',
          type: 'info'
        });
        
        await startWebcamServer();
        // Small delay to ensure webcam server is fully started
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      const response = await stressService.startMonitoring();
      if (response.status === 'success') {
        setStressMonitoring(true);
        setNotification({
          message: 'Stress monitoring started successfully!',
          type: 'success'
        });
        // Start polling for stress data
        startStressDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to start stress monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error starting stress monitoring. Please ensure the backend is running.',
        type: 'error'
      });
    }
  };

  const stopStressMonitoring = async () => {
    try {
      const response = await stressService.stopMonitoring();
      if (response.status === 'success') {
        setStressMonitoring(false);
        setNotification({
          message: 'Stress monitoring stopped successfully!',
          type: 'success'
        });
        // Stop polling
        stopStressDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to stop stress monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error stopping stress monitoring',
        type: 'error'
      });
    }
  };

  // Stress data polling for real-time updates
  const startStressDataPolling = () => {
    // Poll every 30 seconds for stress data
    const interval = setInterval(async () => {
      try {
        // Get recent stress data
        const dataResponse = await stressService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          setStressData(dataResponse.data);
          
          // Check for new alerts
          const alertsResponse = await stressService.getRecentAlerts(10);
          if (alertsResponse.status === 'success') {
            const alerts = alertsResponse.data.alerts;
            setStressAlerts(alerts);
            
            // Show notification for new alerts
            const recentAlert = alerts.find((alert: StressAlert) => 
              !alert.read && new Date(alert.created_at).getTime() > Date.now() - 60000 // Last minute
            );
            
            if (recentAlert) {
              setNotification({
                message: recentAlert.message,
                type: 'warning'
              });
            }
          }
        }
      } catch (error) {
        console.error('Error polling stress data:', error);
      }
    }, 30000);
    
    setStressPollingInterval(interval);
    
    // Get initial data immediately
    setTimeout(async () => {
      try {
        const dataResponse = await stressService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          setStressData(dataResponse.data);
        }
        const alertsResponse = await stressService.getRecentAlerts(10);
        if (alertsResponse.status === 'success') {
          setStressAlerts(alertsResponse.data.alerts);
        }
      } catch (error) {
        console.error('Error getting initial stress data:', error);
      }
    }, 3000);
  };

  const stopStressDataPolling = () => {
    if (stressPollingInterval) {
      clearInterval(stressPollingInterval);
      setStressPollingInterval(null);
    }
    setStressData(null);
    setStressAlerts([]);
  };

  // -----------------------------------------------------------------------------
  // CVS Monitoring Functions
  // -----------------------------------------------------------------------------
  const startCVSMonitoring = async () => {
    try {
      // If webcam server is not active, try to start it first
      if (!webcamServerActive) {
        setNotification({
          message: 'Starting webcam server first...',
          type: 'info'
        });
        
        await startWebcamServer();
        // Small delay to ensure webcam server is fully started
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      const response = await cvsService.startMonitoring();
      if (response.status === 'success') {
        setCvsMonitoring(true);
        setNotification({
          message: 'Eye strain monitoring started successfully!',
          type: 'success'
        });
        // Start polling for CVS data
        startCVSDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to start eye strain monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error starting eye strain monitoring. Please ensure the backend is running.',
        type: 'error'
      });
    }
  };

  const stopCVSMonitoring = async () => {
    try {
      const response = await cvsService.stopMonitoring();
      if (response.status === 'success') {
        setCvsMonitoring(false);
        setNotification({
          message: 'Eye strain monitoring stopped successfully!',
          type: 'success'
        });
        // Stop polling
        stopCVSDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to stop eye strain monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error stopping eye strain monitoring',
        type: 'error'
      });
    }
  };

  // CVS data polling for real-time updates
  const startCVSDataPolling = () => {
    // Poll every 30 seconds for CVS data
    const interval = setInterval(async () => {
      try {
        // Get recent CVS data
        const dataResponse = await cvsService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          console.log('CVS data received:', dataResponse.data);
          setCvsData(dataResponse.data);
          
          // Check for new alerts
          const alertsResponse = await cvsService.getRecentAlerts(10);
          if (alertsResponse.status === 'success') {
            const alerts = alertsResponse.data.alerts;
            setCvsAlerts(alerts);
            
            // Show notification for new alerts
            const recentAlert = alerts.find((alert: CVSAlert) => 
              !alert.read && new Date(alert.created_at).getTime() > Date.now() - 60000 // Last minute
            );
            
            if (recentAlert) {
              setNotification({
                message: recentAlert.message,
                type: 'warning'
              });
            }
          }
        } else {
          console.error('Error getting CVS data:', dataResponse);
        }
      } catch (error) {
        console.error('Error polling CVS data:', error);
      }
    }, 30000);
    
    setCVSPollingInterval(interval);
    
    // Get initial data immediately
    setTimeout(async () => {
      try {
        const dataResponse = await cvsService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          console.log('Initial CVS data received:', dataResponse.data);
          setCvsData(dataResponse.data);
        } else {
          console.warn('Failed to get initial CVS data:', dataResponse);
          // Set default data if none received
          setCvsData({
            predictions: [],
            average: {
              avg_blink_count: 18.0,
              low_blink_count: 0,
              normal_blink_count: 1,
              high_blink_count: 0,
              low_blink_percentage: 0.0,
              normal_blink_percentage: 100.0,
              high_blink_percentage: 0.0,
              total_samples: 1,
              samples: 1
            },
            minutes: 5,
            user_id: null
          });
        }
        
        const alertsResponse = await cvsService.getRecentAlerts(10);
        if (alertsResponse.status === 'success') {
          setCvsAlerts(alertsResponse.data.alerts);
        } else {
          console.warn('Failed to get CVS alerts:', alertsResponse);
        }
      } catch (error) {
        console.error('Error getting initial CVS data:', error);
        // Set default data if error occurs
        setCvsData({
          predictions: [],
          average: {
            avg_blink_count: 18.0,
            low_blink_count: 0,
            normal_blink_count: 1,
            high_blink_count: 0,
            low_blink_percentage: 0.0,
            normal_blink_percentage: 100.0,
            high_blink_percentage: 0.0,
            total_samples: 1,
            samples: 1
          },
          minutes: 5,
          user_id: null
        });
      }
    }, 3000);
  };

  const stopCVSDataPolling = () => {
    if (cvsPollingInterval) {
      clearInterval(cvsPollingInterval);
      setCVSPollingInterval(null);
    }
    setCvsData(null);
    setCvsAlerts([]);
  };

  // -----------------------------------------------------------------------------
  // Hydration Monitoring Functions
  // -----------------------------------------------------------------------------
  const startHydrationMonitoring = async () => {
    setLoading(4); // Use numeric ID for hydration monitoring
    try {
      // First check if webcam server is running
      const statusResponse = await hydrationService.getStatus();
      const webcamServerActive = statusResponse?.data?.webcam_server_active || false;
      
      if (!webcamServerActive) {
        setNotification({
          message: 'Starting webcam server for hydration monitoring...',
          type: 'info'
        });
        
        // Try to start the webcam server first
        try {
          const webcamResponse = await hydrationService.startWebcamServer();
          if (webcamResponse.status !== 'success') {
            // If webcam server fails to start, try using the existing one from posture API
            console.log('Failed to start hydration webcam server, trying posture API...');
            const postureWebcamResponse = await postureService.startWebcamServer();
            
            if (postureWebcamResponse.status !== 'success') {
              setNotification({
                message: 'Failed to start webcam server. Please try again or restart the application.',
                type: 'error'
              });
              setLoading(null);
              return;
            }
          }
        } catch (error) {
          console.error('Error starting webcam server:', error);
          setNotification({
            message: 'Failed to start webcam server. Please check if another application is using your webcam.',
            type: 'error'
          });
          setLoading(null);
          return;
        }
      }
      
      setNotification({
        message: 'Starting hydration monitoring. This may take a moment...',
        type: 'info'
      });
      
      try {
        const response = await hydrationService.startMonitoring();
        
        if (response.status === 'success') {
          setHydrationMonitoring(true);
          setNotification({
            message: 'Hydration monitoring started successfully!',
            type: 'success'
          });
          // Start polling for data
          startHydrationDataPolling();
        } else {
          // If the response indicates an error but the webcam server might be running
          if (response.message && response.message.includes('socket address')) {
            console.log('Socket address error detected, trying with existing webcam server...');
            // The webcam server is likely already running, try again with a different approach
            try {
              // Wait a moment and try again
              await new Promise(resolve => setTimeout(resolve, 2000));
              const retryResponse = await hydrationService.startMonitoring();
              
              if (retryResponse.status === 'success') {
                setHydrationMonitoring(true);
                setNotification({
                  message: 'Hydration monitoring started successfully after retry!',
                  type: 'success'
                });
                // Start polling for data
                startHydrationDataPolling();
                return;
              }
            } catch (retryError) {
              console.error('Error on retry:', retryError);
            }
          }
          
          setNotification({
            message: response.message || 'Failed to start hydration monitoring. Please try again.',
            type: 'error'
          });
        }
      } catch (error) {
        console.error('Error starting hydration monitoring:', error);
        setNotification({
          message: 'Request timed out. The server might be busy or the webcam server might not be running properly.',
          type: 'error'
        });
      }
    } catch (error) {
      console.error('Error in hydration monitoring process:', error);
      setNotification({
        message: 'Error starting hydration monitoring. Please ensure the backend is running.',
        type: 'error'
      });
    } finally {
      setLoading(null);
    }
  };

  const stopHydrationMonitoring = async () => {
    try {
      const response = await hydrationService.stopMonitoring();
      if (response.status === 'success') {
        setHydrationMonitoring(false);
        setNotification({
          message: 'Hydration monitoring stopped successfully!',
          type: 'success'
        });
        // Stop polling
        stopHydrationDataPolling();
      } else {
        setNotification({
          message: response.message || 'Failed to stop hydration monitoring',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Error stopping hydration monitoring',
        type: 'error'
      });
    }
  };

  // Hydration data polling for real-time updates
  const startHydrationDataPolling = () => {
    // Poll every 30 seconds for hydration data
    const interval = setInterval(async () => {
      try {
        // Get recent hydration data
        const dataResponse = await hydrationService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          console.log('Hydration data received:', dataResponse.data);
          setHydrationData(dataResponse.data);
          
          // Check for new alerts
          const alertsResponse = await hydrationService.getRecentAlerts(10);
          if (alertsResponse.status === 'success') {
            const alerts = alertsResponse.data.alerts;
            setHydrationAlerts(alerts);
            
            // Show notification for new alerts
            const recentAlert = alerts.find((alert: HydrationAlert) => 
              !alert.read && new Date(alert.created_at).getTime() > Date.now() - 60000 // Last minute
            );
            
            if (recentAlert) {
              setNotification({
                message: recentAlert.message,
                type: 'warning'
              });
            }
          }
        }
      } catch (error) {
        console.error('Error polling hydration data:', error);
      }
    }, 30000);
    
    setHydrationPollingInterval(interval);
    
    // Get initial data immediately
    setTimeout(async () => {
      try {
        const dataResponse = await hydrationService.getRecentData(5, true);
        if (dataResponse.status === 'success') {
          console.log('Initial hydration data received:', dataResponse.data);
          setHydrationData(dataResponse.data);
        } else {
          console.warn('Failed to get initial hydration data:', dataResponse);
          // Set default data if none received
          setHydrationData({
            predictions: [],
            average: {
              dry_lips_count: 0,
              normal_lips_count: 1,
              dry_lips_percentage: 0.0,
              normal_lips_percentage: 100.0,
              avg_dryness_score: 0.1,
              total_samples: 1,
              samples: 1
            },
            minutes: 5,
            user_id: null
          });
        }
        
        const alertsResponse = await hydrationService.getRecentAlerts(10);
        if (alertsResponse.status === 'success') {
          setHydrationAlerts(alertsResponse.data.alerts);
        } else {
          console.warn('Failed to get hydration alerts:', alertsResponse);
        }
      } catch (error) {
        console.error('Error getting initial hydration data:', error);
        // Set default data if error occurs
        setHydrationData({
          predictions: [],
          average: {
            dry_lips_count: 0,
            normal_lips_count: 1,
            dry_lips_percentage: 0.0,
            normal_lips_percentage: 100.0,
            avg_dryness_score: 0.1,
            total_samples: 1,
            samples: 1
          },
          minutes: 5,
          user_id: null
        });
      }
    }, 3000);
  };

  const stopHydrationDataPolling = () => {
    if (hydrationPollingInterval) {
      clearInterval(hydrationPollingInterval);
      setHydrationPollingInterval(null);
    }
    setHydrationData(null);
    setHydrationAlerts([]);
  };

  // -----------------------------------------------------------------------------
  // Helper Functions
  // -----------------------------------------------------------------------------
  const getPostureStatusColor = () => {
    if (!postureData?.average) return 'default';
    const badPercentage = postureData.average.bad_posture_percentage;
    if (badPercentage > 60) return 'error';
    if (badPercentage > 30) return 'warning';
    return 'success';
  };

  const getStressStatusColor = () => {
    if (!stressData?.average) return 'default';
    const highPercentage = stressData.average.high_stress_percentage;
    if (highPercentage > 60) return 'error';
    if (highPercentage > 30) return 'warning';
    return 'success';
  };

  const getCVSStatusColor = () => {
    if (!cvsData?.average) return 'default';
    
    // Check for abnormal blink rate
    const avgBlinkCount = cvsData.average.avg_blink_count;
    const highPercentage = cvsData.average.high_blink_percentage;
    const lowPercentage = cvsData.average.low_blink_percentage;
    
    if (highPercentage > 60 || lowPercentage > 60) return 'error';
    if (highPercentage > 30 || lowPercentage > 30) return 'warning';
    return 'success';
  };

  const getHydrationStatusColor = () => {
    if (!hydrationData?.average) return 'default';
    
    const dryPercentage = hydrationData.average.dry_lips_percentage;
    if (dryPercentage > 60) return 'error';
    if (dryPercentage > 30) return 'warning';
    return 'success';
  };

  // -----------------------------------------------------------------------------
  // Check Monitoring Status
  // -----------------------------------------------------------------------------
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Check posture monitoring status
        const postureResponse = await postureService.getStatus();
        if (postureResponse.status === 'success') {
          setPostureMonitoring(postureResponse.data.is_monitoring);
          setWebcamServerActive(postureResponse.data.webcam_server_active);
          
          // If monitoring is active, start data polling
          if (postureResponse.data.is_monitoring) {
          startDataPolling();
          }
        }
        
        // Check stress monitoring status
        const stressResponse = await stressService.getStatus();
        if (stressResponse.status === 'success') {
          setStressMonitoring(stressResponse.data.is_monitoring);
          setWebcamServerActive(stressResponse.data.webcam_server_active || webcamServerActive);
          
          // If monitoring is active, start data polling
          if (stressResponse.data.is_monitoring) {
            startStressDataPolling();
          }
        }
        
        // Check CVS monitoring status
        const cvsResponse = await cvsService.getStatus();
        if (cvsResponse.status === 'success') {
          setCvsMonitoring(cvsResponse.data.is_monitoring);
          setWebcamServerActive(cvsResponse.data.webcam_server_active || webcamServerActive);
          
          // If monitoring is active, start data polling
          if (cvsResponse.data.is_monitoring) {
            startCVSDataPolling();
          }
        }
        
        // Check hydration monitoring status
        const hydrationResponse = await hydrationService.getStatus();
        if (hydrationResponse.status === 'success') {
          setHydrationMonitoring(hydrationResponse.data.is_monitoring);
          setWebcamServerActive(hydrationResponse.data.webcam_server_active || webcamServerActive);
          
          // If monitoring is active, start data polling
          if (hydrationResponse.data.is_monitoring) {
            startHydrationDataPolling();
          }
        }
      } catch (error) {
        console.error('Error checking monitoring status:', error);
      }
    };
    
    checkStatus();
    
    // Cleanup on component unmount
    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
      if (stressPollingInterval) clearInterval(stressPollingInterval);
      if (cvsPollingInterval) clearInterval(cvsPollingInterval);
      if (hydrationPollingInterval) clearInterval(hydrationPollingInterval);
    };
  }, []);

  // -----------------------------------------------------------------------------
  // Script Management
  // -----------------------------------------------------------------------------
  const scripts: Script[] = [
    { 
      id: 1, 
      name: 'Enhanced Posture Monitoring', 
      description: 'Monitors your posture in real-time using computer vision',
      icon: <AccessibilityNewIcon />, 
      method: postureMonitoring ? stopPostureMonitoring : startPostureMonitoring,
      color: 'primary',
      isEnhanced: true
    },
    { 
      id: 2, 
      name: 'Stress Detection', 
      description: 'Monitors facial expressions to detect stress levels',
      icon: <SentimentDissatisfiedIcon />, 
      method: stressMonitoring ? stopStressMonitoring : startStressMonitoring,
      color: 'secondary'
    },
    { 
      id: 3, 
      name: 'Eye Strain Detection', 
      description: 'Monitors blink rate to detect eye strain from computer use',
      icon: <VisibilityOffIcon />, 
      method: cvsMonitoring ? stopCVSMonitoring : startCVSMonitoring,
      color: 'info'
    },
    { 
      id: 4, 
      name: 'Dehydration Detection', 
      description: 'Monitors lip dryness to detect dehydration',
      icon: <LocalDrinkIcon />, 
      method: hydrationMonitoring ? stopHydrationMonitoring : startHydrationMonitoring,
      color: 'warning'
    }
  ];

  const runScript = async (scriptId: number) => {
    setLoading(scriptId);
    try {
      const script = scripts.find(s => s.id === scriptId);
      if (script) {
        await script.method();
      }
    } finally {
      setLoading(null);
    }
  };

  const handleCloseNotification = () => {
    setNotification(null);
  };

  // -----------------------------------------------------------------------------
  // Component Render
  // -----------------------------------------------------------------------------
  return (
    <Box sx={{ 
      width: '100%',
      m: 0,
      p: 0
    }}>
      {/* Webcam Server Control */}
      <Paper sx={{ 
        p: { xs: 2, sm: 3 }, 
        mb: 3, 
        display: 'flex', 
        flexDirection: { xs: 'column', sm: 'row' },
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', sm: 'center' },
        gap: 2
      }}>
        <Box>
          <Typography variant="h6" gutterBottom sx={{ mb: 0.5 }}>
            Webcam Server
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {webcamServerActive 
              ? 'Webcam server is running and ready for monitoring tools' 
              : 'Start the webcam server to use monitoring tools'}
          </Typography>
        </Box>
        <Button
          variant="contained"
          color={webcamServerActive ? 'error' : 'success'}
          startIcon={webcamServerActive ? <StopIcon /> : <PlayArrowIcon />}
          onClick={webcamServerActive ? stopWebcamServer : startWebcamServer}
          disabled={webcamLoading}
          sx={{ 
            minWidth: 120,
            alignSelf: { xs: 'stretch', sm: 'auto' }
          }}
        >
          {webcamLoading ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            webcamServerActive ? 'Stop Server' : 'Start Server'
          )}
        </Button>
      </Paper>

      {/* Monitoring Tools */}
      <Typography variant="h5" gutterBottom sx={{ mt: 3, mb: 2 }}>
        Health Monitoring Tools
      </Typography>
      
      <Grid container spacing={2}>
        {scripts.map((script) => (
          <Grid item xs={12} sm={6} md={6} lg={3} key={script.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ 
                flexGrow: 1, 
                display: 'flex', 
                flexDirection: 'column', 
                justifyContent: 'space-between',
                p: 2
              }}>
                <Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ mr: 1, color: `${script.color}.main` }}>
                        {script.icon}
                      </Box>
                      <Typography variant="h6" component="div" fontSize="1rem">
                        {script.name}
                      </Typography>
                    </Box>
                    
                    {/* Status indicator */}
                    {script.id === 1 && postureMonitoring && (
                      <Chip 
                        size="small" 
                        color={getPostureStatusColor() as any} 
                        label="Active" 
                      />
                    )}
                    {script.id === 2 && stressMonitoring && (
                      <Chip 
                        size="small" 
                        color={getStressStatusColor() as any} 
                        label="Active" 
                      />
                    )}
                    {script.id === 3 && cvsMonitoring && (
                      <Chip 
                        size="small" 
                        color={getCVSStatusColor() as any} 
                        label="Active" 
                      />
                    )}
                    {script.id === 4 && hydrationMonitoring && (
                      <Chip 
                        size="small" 
                        color={getHydrationStatusColor() as any} 
                        label="Active" 
                      />
                    )}
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    {script.description}
                  </Typography>
                </Box>
                
                <Button
                  variant="contained"
                  color={
                    (script.id === 1 && postureMonitoring) || 
                    (script.id === 2 && stressMonitoring) ||
                    (script.id === 3 && cvsMonitoring) ||
                    (script.id === 4 && hydrationMonitoring)
                      ? 'error'
                      : 'primary'
                  }
                  fullWidth
                  onClick={() => runScript(script.id)}
                  disabled={loading !== null || (!webcamServerActive && 
                    !(script.id === 1 && postureMonitoring) && 
                    !(script.id === 2 && stressMonitoring) &&
                    !(script.id === 3 && cvsMonitoring) &&
                    !(script.id === 4 && hydrationMonitoring)
                  )}
                  startIcon={
                    loading === script.id ? (
                      <CircularProgress size={24} color="inherit" />
                    ) : (
                      (script.id === 1 && postureMonitoring) ||
                      (script.id === 2 && stressMonitoring) ||
                      (script.id === 3 && cvsMonitoring) ||
                      (script.id === 4 && hydrationMonitoring)
                      ? <StopIcon /> 
                      : <PlayArrowIcon />
                    )
                  }
                >
                  {loading === script.id
                    ? 'Processing...'
                    : (script.id === 1 && postureMonitoring) ||
                      (script.id === 2 && stressMonitoring) ||
                      (script.id === 3 && cvsMonitoring) ||
                      (script.id === 4 && hydrationMonitoring)
                      ? 'Stop Monitoring'
                      : 'Start Monitoring'}
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* CVS Monitoring Dashboard */}
      {cvsMonitoring && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3, mt: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <VisibilityOffIcon color="info" /> Eye Strain Monitoring Dashboard
            </Typography>
            <IconButton onClick={() => setExpandedCVS(!expandedCVS)}>
              {expandedCVS ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={expandedCVS}>
            <Grid container spacing={3}>
              {/* Current Status */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Current Status (Last 5 minutes)
                    </Typography>
                    {cvsData?.average ? (
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Average Blink Rate</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {cvsData.average.avg_blink_count.toFixed(1)} blinks/minute
                          </Typography>
                        </Box>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Low Blink Rate</Typography>
                          <Typography variant="body2" fontWeight="bold" color="warning.main">
                            {cvsData.average.low_blink_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={cvsData.average.low_blink_percentage} 
                          color="warning"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Normal Blink Rate</Typography>
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            {cvsData.average.normal_blink_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={cvsData.average.normal_blink_percentage} 
                          color="success"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">High Blink Rate</Typography>
                          <Typography variant="body2" fontWeight="bold" color="error.main">
                            {cvsData.average.high_blink_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={cvsData.average.high_blink_percentage} 
                          color="error"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Typography variant="caption" color="text.secondary">
                          Total samples: {cvsData.average.total_samples}
                        </Typography>
                        
                        {cvsData.average.low_blink_percentage > 60 && (
                          <Alert severity="warning" sx={{ mt: 2 }}>
                            <strong>Warning:</strong> Low blink rate detected! This may cause dry eyes. Take a break and rest your eyes.
                          </Alert>
                        )}
                        
                        {cvsData.average.high_blink_percentage > 60 && (
                          <Alert severity="warning" sx={{ mt: 2 }}>
                            <strong>Warning:</strong> High blink rate detected! This indicates eye fatigue. Consider taking a break.
                          </Alert>
                        )}
                      </Box>
                    ) : (
                      <Typography color="text.secondary">
                        Collecting data... Please wait for initial readings.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Recent Alerts */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NotificationsActiveIcon color="warning" /> Recent Alerts
                    </Typography>
                    {cvsAlerts.length > 0 ? (
                      <Stack spacing={1} sx={{ maxHeight: 200, overflowY: 'auto' }}>
                        {cvsAlerts.slice(0, 5).map((alert) => (
                          <Alert 
                            key={alert.id} 
                            severity={alert.level as any}
                          >
                            <Typography variant="body2">
                              {alert.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(alert.created_at).toLocaleTimeString()}
                            </Typography>
                          </Alert>
                        ))}
                      </Stack>
                    ) : (
                      <Typography color="text.secondary">
                        No recent alerts. Good eye health!
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Collapse>
        </Paper>
      )}

      {/* Posture Monitoring Dashboard */}
      {postureMonitoring && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccessibilityNewIcon color="primary" /> Posture Monitoring Dashboard
            </Typography>
            <IconButton onClick={() => setExpandedPosture(!expandedPosture)}>
              {expandedPosture ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={expandedPosture}>
            <Grid container spacing={3}>
              {/* Current Status */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Current Status (Last 5 minutes)
                    </Typography>
                    {postureData?.average ? (
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Good Posture</Typography>
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            {postureData.average.good_posture_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={postureData.average.good_posture_percentage} 
                          color="success"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Bad Posture</Typography>
                          <Typography variant="body2" fontWeight="bold" color="error.main">
                            {postureData.average.bad_posture_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={postureData.average.bad_posture_percentage} 
                          color="error"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Typography variant="caption" color="text.secondary">
                          Total samples: {postureData.average.total_samples}
                        </Typography>
                        
                        {postureData.average.bad_posture_percentage > 60 && (
                          <Alert severity="warning" sx={{ mt: 2 }}>
                            <strong>Warning:</strong> Poor posture detected! Please adjust your sitting position.
                          </Alert>
                        )}
                      </Box>
                    ) : (
                      <Typography color="text.secondary">
                        Collecting data... Please wait for initial readings.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Recent Alerts */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NotificationsActiveIcon color="warning" /> Recent Alerts
                    </Typography>
                    {postureAlerts.length > 0 ? (
                      <Stack spacing={1} sx={{ maxHeight: 200, overflowY: 'auto' }}>
                        {postureAlerts.slice(0, 5).map((alert) => (
                          <Alert 
                            key={alert.id} 
                            severity={alert.level as any}
                          >
                            <Typography variant="body2">
                              {alert.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(alert.created_at).toLocaleTimeString()}
                            </Typography>
                          </Alert>
                        ))}
                      </Stack>
                    ) : (
                      <Typography color="text.secondary">
                        No recent alerts. Good posture!
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Collapse>
        </Paper>
      )}

      {/* Stress Monitoring Dashboard */}
      {stressMonitoring && (
        <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SentimentDissatisfiedIcon color="secondary" /> Stress Monitoring Dashboard
            </Typography>
            <IconButton onClick={() => setExpandedStress(!expandedStress)}>
              {expandedStress ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={expandedStress}>
            <Grid container spacing={3}>
              {/* Current Status */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Current Status (Last 5 minutes)
                    </Typography>
                    {stressData?.average ? (
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Low Stress</Typography>
                          <Typography variant="body2" fontWeight="bold" color="success.main">
                            {stressData.average.low_stress_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={stressData.average.low_stress_percentage} 
                          color="success"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Medium Stress</Typography>
                          <Typography variant="body2" fontWeight="bold" color="warning.main">
                            {stressData.average.medium_stress_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={stressData.average.medium_stress_percentage} 
                          color="warning"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">High Stress</Typography>
                          <Typography variant="body2" fontWeight="bold" color="error.main">
                            {stressData.average.high_stress_percentage.toFixed(1)}%
                          </Typography>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={stressData.average.high_stress_percentage} 
                          color="error"
                          sx={{ mb: 2, height: 8, borderRadius: 1 }}
                        />
                        
                        <Typography variant="caption" color="text.secondary">
                          Total samples: {stressData.average.total_samples}
                        </Typography>
                        
                        {stressData.average.high_stress_percentage > 60 && (
                          <Alert severity="warning" sx={{ mt: 2 }}>
                            <strong>Warning:</strong> High stress levels detected! Consider taking a short break or doing some relaxation exercises.
                          </Alert>
                        )}
                      </Box>
                    ) : (
                      <Typography color="text.secondary">
                        Collecting data... Please wait for initial readings.
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              {/* Recent Alerts */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <NotificationsActiveIcon color="warning" /> Recent Alerts
                    </Typography>
                    {stressAlerts.length > 0 ? (
                      <Stack spacing={1} sx={{ maxHeight: 200, overflowY: 'auto' }}>
                        {stressAlerts.slice(0, 5).map((alert) => (
                          <Alert 
                            key={alert.id} 
                            severity={alert.level as any}
                          >
                            <Typography variant="body2">
                              {alert.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(alert.created_at).toLocaleTimeString()}
                            </Typography>
                          </Alert>
                        ))}
                      </Stack>
                    ) : (
                      <Typography color="text.secondary">
                        No recent alerts. Stress levels are good!
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Collapse>
        </Paper>
      )}

      {/* Notifications */}
      {notification && (
      <Snackbar 
          open={true}
        autoHideDuration={6000} 
        onClose={handleCloseNotification}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseNotification} severity={notification.type} sx={{ width: '100%' }}>
            {notification.message}
          </Alert>
      </Snackbar>
      )}
    </Box>
  );
};

export default ScriptRunner; 