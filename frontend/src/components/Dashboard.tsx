import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Paper,
  Alert,
  Chip,
  Divider,
  Stack,
  LinearProgress,
  Avatar,
  CircularProgress,
  useTheme,
  useMediaQuery,
  Card,
  CardContent,
} from '@mui/material';
import Webcam from 'react-webcam';
import { useAuth } from '../contexts/AuthContext';
import Layout from './Layout';
import { monitoringService } from '../services/api';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import VideocamIcon from '@mui/icons-material/Videocam';
import AssessmentIcon from '@mui/icons-material/Assessment';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TimelineIcon from '@mui/icons-material/Timeline';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import PersonIcon from '@mui/icons-material/Person';
import ScriptRunner from './ScriptRunner';

// Real activity data will come from the backend
const activityData = [
  { name: 'Focus', percentage: 80, color: '#4caf50' },
  { name: 'Distraction', percentage: 15, color: '#ff9800' },
  { name: 'Away', percentage: 5, color: '#f44336' }
];

const Dashboard: React.FC = () => {
  const webcamRef = useRef<Webcam>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [alert, setAlert] = useState<string | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const { user, userProfile, profileLoading, refreshProfile } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));

  // Don't auto-refresh the profile when component mounts to avoid excessive API calls
  // useEffect(() => {
  //   // Refresh profile on component mount
  //   refreshProfile();
  // }, [refreshProfile]);

  const startMonitoring = useCallback(async () => {
    if (!showCamera) {
      setShowCamera(true);
      return;
    }
    
    try {
      const response = await monitoringService.startMonitoring();
      if (response.status === 'success') {
        setIsMonitoring(true);
        setAlert(null);
      } else {
        setAlert(`Failed to start monitoring: ${response.message}`);
      }
    } catch (error) {
      console.error('Error starting monitoring:', error);
      setAlert('Failed to connect to the backend. Make sure the Python server is running.');
    }
  }, [showCamera]);

  const stopMonitoring = useCallback(async () => {
    try {
      const response = await monitoringService.stopMonitoring();
      if (response.status === 'success') {
        setIsMonitoring(false);
        setAlert(null);
      } else {
        setAlert(`Failed to stop monitoring: ${response.message}`);
      }
    } catch (error) {
      console.error('Error stopping monitoring:', error);
      setAlert('Failed to connect to the backend. Make sure the Python server is running.');
    }
  }, []);

  // Get formatted user display name
  const displayName = userProfile?.displayName || 
                     userProfile?.email?.split('@')[0] || 
                     user?.email?.split('@')[0] || 
                     'Student';
  
  // Get user initials for avatar
  const userInitials = displayName.substring(0, 2).toUpperCase();

  const handleProfileRefresh = async () => {
    try {
      await refreshProfile();
    } catch (error) {
      console.error('Error refreshing profile:', error);
      setAlert('Error refreshing profile. Please try again later.');
    }
  };

  return (
    <Layout title="Dashboard">
      {alert && (
        <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setAlert(null)}>
          {alert}
        </Alert>
      )}

      <Grid container spacing={isMobile ? 2 : 3}>
        {/* Welcome card with user profile */}
        <Grid item xs={12}>
          <Paper sx={{ 
            p: { xs: 2, sm: 3 }, 
            mb: 3,
            display: 'flex',
            flexDirection: isMobile ? 'column' : 'row',
            justifyContent: 'space-between', 
            alignItems: isMobile ? 'flex-start' : 'center',
            gap: isMobile ? 2 : 1
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {profileLoading ? (
                <CircularProgress size={40} />
              ) : (
                <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
                  {userInitials}
                </Avatar>
              )}
              <Box>
                <Typography variant="h5" gutterBottom sx={{ mb: 0.5 }}>
                  Welcome back, {displayName}!
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {userProfile?.email || user?.email || 'Loading profile...'}
                </Typography>
                {userProfile?.lastLogin && (
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                    Last login: {new Date(userProfile.lastLogin).toLocaleString()}
                  </Typography>
                )}
              </Box>
            </Box>
            <Button
              variant="contained"
              color={isMonitoring ? "error" : "primary"}
              startIcon={isMonitoring ? <StopIcon /> : <PlayArrowIcon />}
              onClick={isMonitoring ? stopMonitoring : startMonitoring}
              size={isMobile ? "medium" : "large"}
              sx={{ minWidth: 160 }}
            >
              {isMonitoring ? "Stop Monitoring" : showCamera ? "Start Monitoring" : "Activate Camera"}
            </Button>
          </Paper>
        </Grid>

        {/* Profile card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ height: '100%', p: { xs: 2, sm: 3 } }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
              <PersonIcon color="primary" /> Profile
            </Typography>
            {profileLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Display Name
                  </Typography>
                  <Typography variant="body1" fontWeight="medium" sx={{ wordBreak: "break-word" }}>
                    {userProfile?.displayName || displayName}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Email
                  </Typography>
                  <Typography variant="body1" sx={{ wordBreak: "break-all" }}>
                    {userProfile?.email || user?.email}
                  </Typography>
                </Box>
                {userProfile?.createdAt && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Account Created
                    </Typography>
                    <Typography variant="body1">
                      {new Date(userProfile.createdAt).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}
                <Box sx={{ mt: 'auto', pt: 2 }}>
                  <Button 
                    variant="outlined" 
                    size="small" 
                    onClick={handleProfileRefresh}
                    fullWidth
                  >
                    Refresh Profile
                  </Button>
                </Box>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Script Runner Section */}
        <Grid item xs={12} md={8}>
          <ScriptRunner />
        </Grid>

        {/* Camera view */}
        {showCamera && (
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: { xs: 2, sm: 3 }, height: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <VideocamIcon color="primary" /> Camera Feed
                </Typography>
                <Chip 
                  label={isMonitoring ? "Monitoring Active" : "Monitoring Inactive"} 
                  color={isMonitoring ? "success" : "default"}
                  size="small"
                />
              </Box>
              <Box 
                sx={{ 
                  flex: 1, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  backgroundColor: '#f0f0f0',
                  borderRadius: 1,
                  overflow: 'hidden',
                  minHeight: { xs: 200, sm: 300, md: 350 },
                }}
              >
                <Webcam
                  ref={webcamRef}
                  audio={false}
                  width="100%"
                  height="auto"
                  screenshotFormat="image/jpeg"
                  videoConstraints={{
                    facingMode: "user"
                  }}
                />
              </Box>
              {isMonitoring && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Current session: 00:00:00
                  </Typography>
                  <LinearProgress variant="determinate" value={0} color="primary" />
                </Box>
              )}
            </Paper>
          </Grid>
        )}

        {/* Activity stats - only show when monitoring is active or there's data */}
        {isMonitoring && (
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: { xs: 2, sm: 3 }, height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon color="primary" /> Activity Analysis
              </Typography>
              <Box sx={{ mb: 3 }}>
                {activityData.map((activity) => (
                  <Box key={activity.name} sx={{ mb: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="body2">{activity.name}</Typography>
                      <Typography variant="body2" fontWeight="medium">{activity.percentage}%</Typography>
                    </Box>
                    <LinearProgress 
                      variant="determinate" 
                      value={activity.percentage} 
                      sx={{ 
                        height: 8, 
                        borderRadius: 1,
                        backgroundColor: 'rgba(0,0,0,0.1)',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: activity.color
                        }
                      }} 
                    />
                  </Box>
                ))}
              </Box>
              
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button 
                  variant="outlined" 
                  startIcon={<TimelineIcon />}
                  fullWidth
                >
                  View Detailed Analysis
                </Button>
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>
    </Layout>
  );
};

export default Dashboard; 