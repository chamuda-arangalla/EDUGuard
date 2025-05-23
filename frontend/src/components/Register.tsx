import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Link,
  Alert,
  Paper,
  Avatar,
  Grid,
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
import PersonIcon from '@mui/icons-material/Person';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import Logo from './Logo';

const Register: React.FC = () => {
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      return setError('Passwords do not match');
    }

    try {
      setError('');
      setLoading(true);
      
      // Optionally pass displayName if provided
      await register(email, password, displayName || undefined);
      
      // Show success message
      setRegistrationSuccess(true);
      
      // Navigate to login page after 2 seconds
      setTimeout(() => {
        navigate('/login', { state: { registrationSuccess: true } });
      }, 2500); // Increased to 2.5 seconds for better visibility
      
    } catch (err) {
      console.error('Registration error:', err);
      
      if (err instanceof FirebaseError) {
        switch (err.code) {
          case 'auth/email-already-in-use':
            setError('Email is already in use. Please try logging in instead.');
            break;
          case 'auth/invalid-email':
            setError('Invalid email address format.');
            break;
          case 'auth/weak-password':
            setError('Password is too weak. Please use at least 6 characters.');
            break;
          case 'auth/network-request-failed':
            setError('Network error. Please check your internet connection.');
            break;
          default:
            setError(`Registration failed: ${err.message}`);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to create an account. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePassword = () => {
    setShowPassword(prev => !prev);
  };

  const handleToggleConfirmPassword = () => {
    setShowConfirmPassword(prev => !prev);
  };

  return (
    <Container component="main" maxWidth="lg" sx={{ height: '100vh', display: 'flex', alignItems: 'center' }}>
      <Snackbar
        open={registrationSuccess}
        autoHideDuration={2500}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <MuiAlert 
          elevation={6} 
          variant="filled" 
          severity="success" 
          icon={<CheckCircleOutlineIcon />}
          sx={{ width: '100%', fontSize: '1rem' }}
        >
          Registration successful! Redirecting to login...
        </MuiAlert>
      </Snackbar>
      
      <Grid container spacing={0} sx={{ height: '70vh' }}>
        {/* Left side - Welcome graphic */}
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
              Join EDUGuard
            </Typography>
            <Typography variant="h6" sx={{ color: 'rgba(255, 255, 255, 0.9)', mb: 3 }}>
              Create your account to start monitoring your focus
            </Typography>
            <Logo size={100} />
            <Typography variant="body1" sx={{ color: 'rgba(255, 255, 255, 0.8)', mt: 3 }}>
              EDUGuard helps students maintain focus during study sessions using advanced machine learning techniques.
            </Typography>
          </Box>
        </Grid>
        
        {/* Right side - Register form */}
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
                  Create Account
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Fill out the form to register
                </Typography>
              </Box>
              
              {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
              
              <Box component="form" onSubmit={handleSubmit}>
                <TextField
                  margin="normal"
                  fullWidth
                  id="displayName"
                  label="Display Name (Optional)"
                  name="displayName"
                  autoComplete="name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PersonIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
                
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
                  autoComplete="new-password"
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
                
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  name="confirmPassword"
                  label="Confirm Password"
                  type={showConfirmPassword ? "text" : "password"}
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LockIcon color="action" />
                      </InputAdornment>
                    ),
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle confirm password visibility"
                          onClick={handleToggleConfirmPassword}
                          edge="end"
                        >
                          {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
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
                  {loading ? 'Creating Account...' : 'Register'}
                </Button>
                
                <Box sx={{ textAlign: 'center' }}>
                  <Link component={RouterLink} to="/login" variant="body2" sx={{ color: 'primary.main' }}>
                    {"Already have an account? Sign In"}
                  </Link>
                </Box>
              </Box>
            </Paper>
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Register; 