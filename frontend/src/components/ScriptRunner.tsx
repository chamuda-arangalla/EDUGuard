import React, { useState, useEffect } from 'react';
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
import { postureService, stressService } from '../services/api';

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

const ScriptRunner: React.FC = () => {
  const [loading, setLoading] = useState<number | null>(null);
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error' | 'warning' | 'info'} | null>(null);
  const [postureMonitoring, setPostureMonitoring] = useState(false);
  const [postureData, setPostureData] = useState<PostureData | null>(null);
  const [postureAlerts, setPostureAlerts] = useState<PostureAlert[]>([]);
  const [expandedPosture, setExpandedPosture] = useState(false);
  const [stressMonitoring, setStressMonitoring] = useState(false);
  const [stressData, setStressData] = useState<StressData | null>(null);
  const [stressAlerts, setStressAlerts] = useState<StressAlert[]>([]);
  const [expandedStress, setExpandedStress] = useState(false);
  const [webcamServerActive, setWebcamServerActive] = useState(false);
  const [webcamLoading, setWebcamLoading] = useState(false);

  // Webcam server control functions
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

  // Enhanced posture monitoring functions
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

  // Stress monitoring functions
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

  // Data polling for real-time updates
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

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

  // Stress data polling for real-time updates
  const [stressPollingInterval, setStressPollingInterval] = useState<NodeJS.Timeout | null>(null);

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

  // Check monitoring status on component mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        // Check posture status
        const postureResponse = await postureService.getStatus();
        if (postureResponse.status === 'success') {
          // Set posture monitoring status
          if (postureResponse.data.is_monitoring) {
            setPostureMonitoring(true);
            startDataPolling();
          }
          
          // Set webcam server status
          if (postureResponse.data.webcam_server_active) {
            setWebcamServerActive(true);
          }
        }
        
        // Check stress status
        const stressResponse = await stressService.getStatus();
        if (stressResponse.status === 'success') {
          // Set stress monitoring status
          if (stressResponse.data.is_monitoring) {
            setStressMonitoring(true);
            startStressDataPolling();
          }
          
          // Also check webcam server from stress API if it wasn't active in posture API
          if (!postureResponse.data?.webcam_server_active && stressResponse.data.webcam_server_active) {
            setWebcamServerActive(true);
          }
        }
      } catch (error) {
        console.error('Error checking monitoring status:', error);
      }
    };
    
    checkStatus();
    
    // Cleanup on unmount
    return () => {
      stopDataPolling();
      stopStressDataPolling();
    };
  }, []);

  const scripts: Script[] = [
    { 
      id: 1, 
      name: 'Enhanced Posture Checking', 
      description: 'Real-time posture monitoring with Firebase integration and smart alerts', 
      icon: <AccessibilityNewIcon />, 
      method: postureMonitoring ? stopPostureMonitoring : startPostureMonitoring,
      color: 'primary',
      isEnhanced: true
    },
    { 
      id: 2, 
      name: 'Stress Level Checking', 
      description: 'Detects signs of stress and recommends breaks', 
      icon: <SentimentDissatisfiedIcon />, 
      method: stressMonitoring ? stopStressMonitoring : startStressMonitoring,
      color: 'secondary'
    },
    { 
      id: 3, 
      name: 'Eye Strain Checking', 
      description: 'Monitors for eye strain and suggests exercises', 
      icon: <VisibilityOffIcon />, 
      method: () => window?.electron?.runScript3(),
      color: 'success'
    },
    { 
      id: 4, 
      name: 'Dehydration Checking', 
      description: 'Reminds to drink water during study sessions', 
      icon: <LocalDrinkIcon />, 
      method: () => window?.electron?.runScript4(),
      color: 'info'
    }
  ];

  const runScript = async (id: number, method: () => Promise<any>) => {
    // Special handling for enhanced posture monitoring
    if (id === 1) {
      try {
        setLoading(id);
        await method();
      } catch (error) {
        console.error(`Error running enhanced posture monitoring:`, error);
        setNotification({ 
          message: `Failed to manage posture monitoring: ${(error as Error).message || 'Unknown error'}`, 
          type: 'error' 
        });
      } finally {
        setLoading(null);
      }
      return;
    }
    
    // Original script handling for other scripts
    try {
      setLoading(id);
      const result = await method();
      setNotification({ 
        message: `Successfully activated ${scripts.find(s => s.id === id)?.name}`, 
        type: 'success' 
      });
    } catch (error) {
      console.error(`Error running script ${id}:`, error);
      setNotification({ 
        message: `Failed to run script: ${(error as Error).message || 'Unknown error'}`, 
        type: 'error' 
      });
    } finally {
      setLoading(null);
    }
  };

  const handleCloseNotification = () => {
    setNotification(null);
  };

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

  return (
    <Box>
      {/* Webcam Server Control */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PlayArrowIcon color="primary" /> Webcam Server Control
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Start the webcam server separately before running monitoring tools. This allows for more control over system resources.
        </Typography>
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            variant={webcamServerActive ? "contained" : "outlined"}
            color={webcamServerActive ? "error" : "primary"}
            size="large"
            startIcon={webcamLoading ? <CircularProgress size={20} /> : webcamServerActive ? <StopIcon /> : <PlayArrowIcon />}
            onClick={webcamServerActive ? stopWebcamServer : startWebcamServer}
            disabled={webcamLoading || (webcamServerActive && (postureMonitoring || stressMonitoring))}
            sx={{ 
              px: 4,
              py: 1.5,
              border: 2,
              '&:hover': {
                border: 2,
              }
            }}
          >
            {webcamServerActive ? 'Stop Webcam Server' : 'Start Webcam Server'}
          </Button>
          
          <Chip 
            label={webcamServerActive ? "Active" : "Inactive"} 
            color={webcamServerActive ? "success" : "default"} 
            variant="outlined"
          />
          
          {webcamServerActive && (postureMonitoring || stressMonitoring) && (
            <Typography variant="caption" color="warning.main">
              Cannot stop webcam server while monitoring tools are active.
            </Typography>
          )}
        </Box>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PlayArrowIcon color="primary" /> Health Monitoring Tools
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Activate any of the monitoring tools below to help maintain your health and productivity during study sessions.
          System notifications will appear when health concerns are detected.
        </Typography>

        <Grid container spacing={2}>
          {scripts.map((script) => (
            <Grid item xs={12} sm={6} key={script.id}>
              <Button
                variant={
                  (script.id === 1 && postureMonitoring) || 
                  (script.id === 2 && stressMonitoring) 
                    ? "contained" 
                    : "outlined"
                }
                color={script.color}
                fullWidth
                size="large"
                startIcon={
                  loading === script.id ? 
                    <CircularProgress size={20} /> : 
                    ((script.id === 1 && postureMonitoring) || 
                     (script.id === 2 && stressMonitoring)) 
                      ? <StopIcon /> 
                      : script.icon
                }
                onClick={() => runScript(script.id, script.method)}
                disabled={loading !== null}
                sx={{ 
                  py: 2, 
                  justifyContent: 'flex-start',
                  border: 2,
                  '&:hover': {
                    border: 2,
                  }
                }}
              >
                <Box sx={{ textAlign: 'left', flex: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {script.id === 1 && postureMonitoring 
                      ? 'Stop Posture Monitoring' 
                      : script.id === 2 && stressMonitoring 
                        ? 'Stop Stress Monitoring'
                        : script.name
                    }
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {script.description}
                  </Typography>
                  {((script.id === 1 && postureMonitoring) || 
                    (script.id === 2 && stressMonitoring)) && (
                    <Chip 
                      label="Active" 
                      color="success" 
                      size="small" 
                      sx={{ mt: 0.5 }}
                    />
                  )}
                </Box>
              </Button>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
          <CheckCircleIcon color="success" fontSize="small" />
          <Typography variant="body2" color="text.secondary">
            Each health monitoring tool will generate system notifications to remind you even when the app is minimized.
          </Typography>
        </Box>
      </Paper>

      {/* Enhanced Posture Monitoring Dashboard */}
      {postureMonitoring && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AccessibilityNewIcon color="primary" /> Posture Monitoring Dashboard
            </Typography>
            <IconButton onClick={() => setExpandedPosture(!expandedPosture)}>
              {expandedPosture ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={expandedPosture}>
            <Grid container spacing={2}>
              {/* Current Status */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
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
                            <strong>Warning:</strong> High bad posture detected! Please adjust your sitting position.
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
                  <CardContent>
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
                        No recent alerts. Good posture maintained!
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
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SentimentDissatisfiedIcon color="secondary" /> Stress Monitoring Dashboard
            </Typography>
            <IconButton onClick={() => setExpandedStress(!expandedStress)}>
              {expandedStress ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>

          <Collapse in={expandedStress}>
            <Grid container spacing={2}>
              {/* Current Status */}
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
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
                            <strong>Warning:</strong> High stress detected! Please take a break.
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
                  <CardContent>
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
                        No recent alerts. Good stress management!
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Collapse>
        </Paper>
      )}

      <Snackbar 
        open={notification !== null} 
        autoHideDuration={6000} 
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification?.type as 'success' | 'error' | 'warning' | 'info'} 
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification?.message || ''}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ScriptRunner; 