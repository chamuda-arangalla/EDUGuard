import React, { useState } from 'react';
import { Button, Box, Typography, CircularProgress, Paper, Alert, Grid, Card, CardContent } from '@mui/material';
import { monitoringService } from '../services/api';
import Layout from './Layout';
import SettingsIcon from '@mui/icons-material/Settings';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

const Settings: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const testConnection = async (action: 'start' | 'stop') => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = action === 'start' 
        ? await monitoringService.startMonitoring()
        : await monitoringService.stopMonitoring();
      
      setResult(response);
    } catch (err) {
      console.error('Backend connection error:', err);
      setError('Failed to connect to the backend. Make sure the Python server is running.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout title="Settings">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <SettingsIcon color="primary" /> Backend Connection
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Test the connection between the desktop app and the Python backend.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Connection Test</Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Use these controls to test if the desktop application can communicate with the Python backend for monitoring services.
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
              <Button 
                variant="contained" 
                color="primary"
                onClick={() => testConnection('start')}
                disabled={isLoading}
                startIcon={<PlayArrowIcon />}
                sx={{ px: 3 }}
              >
                Start Monitoring
              </Button>
              
              <Button 
                variant="outlined" 
                color="secondary"
                onClick={() => testConnection('stop')}
                disabled={isLoading}
                startIcon={<StopIcon />}
                sx={{ px: 3 }}
              >
                Stop Monitoring
              </Button>
            </Box>
            
            {isLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                <CircularProgress />
              </Box>
            )}
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            {result && (
              <Alert 
                severity={result.status === 'success' ? 'success' : 'warning'}
                icon={result.status === 'success' ? <CheckCircleIcon /> : <ErrorIcon />}
                sx={{ mb: 2 }}
              >
                <Typography variant="subtitle2">
                  Status: {result.status}
                </Typography>
                <Typography variant="body2">
                  Message: {result.message}
                </Typography>
              </Alert>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Connection Status</Typography>
            
            <Card 
              variant="outlined" 
              sx={{ 
                mb: 2, 
                bgcolor: result?.status === 'success' ? 'success.light' : error ? 'error.light' : 'grey.100',
                color: result?.status === 'success' || error ? 'white' : 'inherit'
              }}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                {result?.status === 'success' ? (
                  <CheckCircleIcon sx={{ fontSize: 60, color: 'white' }} />
                ) : error ? (
                  <ErrorIcon sx={{ fontSize: 60, color: 'white' }} />
                ) : (
                  <SettingsIcon sx={{ fontSize: 60, color: 'text.secondary' }} />
                )}
                
                <Typography variant="h6" sx={{ mt: 2 }}>
                  {result?.status === 'success' 
                    ? 'Backend Connected' 
                    : error 
                    ? 'Connection Failed' 
                    : 'No Connection Test Run'}
                </Typography>
                
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {result?.status === 'success' 
                    ? 'The desktop app is successfully connected to the Python backend.' 
                    : error 
                    ? 'Check if the Python server is running on port 5000.' 
                    : 'Click one of the buttons to test the connection.'}
                </Typography>
              </CardContent>
            </Card>
            
            <Typography variant="body2" color="text.secondary">
              The backend server provides machine learning capabilities for monitoring student activities during study sessions.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Layout>
  );
};

export default Settings; 