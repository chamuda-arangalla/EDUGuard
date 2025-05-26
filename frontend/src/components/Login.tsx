import React, { useState, useEffect } from 'react';
import { useNavigate, Link as RouterLink, useLocation } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Link,
  Alert,
  Paper,
  Grid,
  Avatar,
  InputAdornment,
  IconButton,
  Snackbar,
  Alert as MuiAlert,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { FirebaseError } from 'firebase/app';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import EmailIcon from '@mui/icons-material/Email';
import LockIcon from '@mui/icons-material/Lock';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import Logo from '../assets/logo.png';

interface LocationState {
  registrationSuccess?: boolean;
  from?: string;
}

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string | null>(null);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  // Check for registration success message from navigation state
  useEffect(() => {
    const state = location.state as LocationState;
    if (state && state.registrationSuccess) {
      setRegistrationSuccess(true);
      
      // Clear the state to prevent showing the message on page refresh
      navigate(location.pathname, { replace: true });
      
      // Auto-hide after a few seconds
      setTimeout(() => {
        setRegistrationSuccess(false);
      }, 3000);
    }
  }, [location, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError('');
      setDebugInfo(null);
      setLoading(true);
      console.log('Attempting login with:', email);
      
      await login(email, password);
      
      // Show success message
      setLoginSuccess(true);
      
      // Wait longer before redirecting to ensure the popup is seen
      setTimeout(() => {
        console.log('Login successful, navigating to dashboard');
        navigate('/');
      }, 2000); // Increased from 1000ms to 2000ms
      
    } catch (err) {
      console.error('Login error:', err);
      
      if (err instanceof FirebaseError) {
        switch (err.code) {
          case 'auth/invalid-email':
            setError('Invalid email address');
            break;
          case 'auth/user-disabled':
            setError('This account has been disabled');
            break;
          case 'auth/user-not-found':
            setError('No account found with this email');
            break;
          case 'auth/wrong-password':
            setError('Incorrect password');
            break;
          case 'auth/network-request-failed':
            setError('Network error. Please check your internet connection.');
            break;
          case 'auth/too-many-requests':
            setError('Too many failed login attempts. Please try again later.');
            break;
          default:
            setError(`Authentication error (${err.code}): ${err.message}`);
            setDebugInfo(JSON.stringify({
              code: err.code,
              message: err.message,
              name: err.name,
            }));
        }
      } else if (err instanceof Error) {
        setError(`Login failed: ${err.message}`);
        setDebugInfo(err.stack || 'No stack trace available');
      } else {
        setError('Failed to sign in. Unknown error.');
        setDebugInfo(JSON.stringify(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePassword = () => {
    setShowPassword(prev => !prev);
  };

  return (
    <Container component="main" maxWidth="lg" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
      {/* Success messages with improved visibility */}
      <Snackbar
        open={registrationSuccess}
        autoHideDuration={3000}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MuiAlert 
          elevation={6} 
          variant="filled" 
          severity="success"
          icon={<CheckCircleOutlineIcon />}
          sx={{ width: '100%', fontSize: '1rem' }}
        >
          Registration successful! Please log in with your credentials.
        </MuiAlert>
      </Snackbar>
      
      <Snackbar
        open={loginSuccess}
        autoHideDuration={2000}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MuiAlert 
          elevation={6} 
          variant="filled" 
          severity="success" 
          icon={<CheckCircleOutlineIcon />}
          sx={{ width: '100%', fontSize: '1rem' }}
        >
          Login successful! Redirecting to dashboard...
        </MuiAlert>
      </Snackbar>
      
      <Grid container spacing={0} sx={{ height: '70vh' }}>
        {/* Left side - Login form */}
        <Grid item xs={12} md={6}>
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              p: 4,
            }}
          >
            <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 450, borderRadius: 4 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
                <Avatar sx={{ m: 1, bgcolor: 'primary.main' }}>
                  <LockOutlinedIcon />
                </Avatar>
                <Typography component="h1" variant="h5" fontWeight="bold">
                  Sign in to EDUGuard
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Enter your credentials to access your account
                </Typography>
              </Box>
              
              {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
              
              {debugInfo && process.env.NODE_ENV !== 'production' && (
                <Alert severity="info" sx={{ mb: 3, overflowX: 'auto' }}>
                  <Typography variant="caption" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.7rem' }}>
                    {debugInfo}
                  </Typography>
                </Alert>
              )}
              
              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="email"
                  label="Email Address"
                  name="email"
                  autoComplete="email"
                  autoFocus
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <EmailIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  name="password"
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  id="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={handleTogglePassword}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 3, mb: 2, py: 1.5 }}
                  disabled={loading}
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
                <Box sx={{ textAlign: 'center' }}>
                  <Link component={RouterLink} to="/register" variant="body2" sx={{ color: 'primary.main' }}>
                    {"Don't have an account? Sign Up"}
                  </Link>
                </Box>
              </Box>
            </Paper>
          </Box>
        </Grid>
        
        {/* Right side - Welcome graphic */}
        <Grid item xs={12} md={6} sx={{ display: { xs: 'none', md: 'block' } }}>
          <Box
            sx={{
              height: '100%',
              bgcolor: 'primary.light',
              borderRadius: 4,
              p: 5,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}
          >
            <Typography variant="h3" component="h2" sx={{ color: 'white', fontWeight: 'bold', mb: 2 }}>
              Welcome to EDUGuard
            </Typography>
            <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 3 }}>
              The ultimate desktop application for student focus monitoring
            </Typography>
            <img src={Logo} alt="Logo" style={{ width: '100%', height: 'auto' }} />
            <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.8)', mt: 3 }}>
              EDUGuard helps students maintain focus during study sessions using advanced machine learning techniques.
            </Typography>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Login; 