import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Grid, 
  Typography, 
  Paper, 
  Snackbar, 
  Alert,
  CircularProgress
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AccessibilityNewIcon from '@mui/icons-material/AccessibilityNew';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LocalDrinkIcon from '@mui/icons-material/LocalDrink';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

type ScriptColor = 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error';

interface Script {
  id: number;
  name: string;
  description: string;
  icon: React.ReactNode;
  method: () => Promise<any>;
  color: ScriptColor;
}

const ScriptRunner: React.FC = () => {
  const [loading, setLoading] = useState<number | null>(null);
  const [notification, setNotification] = useState<{message: string, type: 'success' | 'error'} | null>(null);

  const scripts: Script[] = [
    { 
      id: 1, 
      name: 'Posture Checking', 
      description: 'Monitors and alerts about poor sitting posture', 
      icon: <AccessibilityNewIcon />, 
      method: () => window?.electron?.runScript1(),
      color: 'primary'
    },
    { 
      id: 2, 
      name: 'Stress Level Checking', 
      description: 'Detects signs of stress and recommends breaks', 
      icon: <SentimentDissatisfiedIcon />, 
      method: () => window?.electron?.runScript2(),
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

  return (
    <Box>
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
                variant="outlined"
                color={script.color}
                fullWidth
                size="large"
                startIcon={loading === script.id ? <CircularProgress size={20} /> : script.icon}
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
                <Box sx={{ textAlign: 'left' }}>
                  <Typography variant="subtitle1" fontWeight="bold">{script.name}</Typography>
                  <Typography variant="body2" color="text.secondary">{script.description}</Typography>
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

      <Snackbar 
        open={notification !== null} 
        autoHideDuration={5000} 
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        {notification && (
          <Alert 
            onClose={handleCloseNotification} 
            severity={notification.type} 
            variant="filled"
            sx={{ width: '100%' }}
          >
            {notification.message}
          </Alert>
        )}
      </Snackbar>
    </Box>
  );
};

export default ScriptRunner; 