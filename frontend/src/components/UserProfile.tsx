import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { readData, updateData, subscribeToData } from '../services/database';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Paper, 
  CircularProgress, 
  Alert,
  Grid,
  Avatar,
  Divider,
  IconButton,
  Snackbar,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import Layout from './Layout';

interface UserProfileData {
  displayName?: string;
  bio?: string;
  phone?: string;
  email?: string;
  school?: string;
  lastUpdated?: number;
  [key: string]: any;
}

const UserProfile: React.FC = () => {
  const { user, userProfile, refreshProfile } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [profile, setProfile] = useState<UserProfileData>({
    displayName: '',
    bio: '',
    phone: '',
    email: user?.email || '',
    school: ''
  });
  
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isMedium = useMediaQuery(theme.breakpoints.down('md'));

  useEffect(() => {
    if (!user?.uid) {
      setLoading(false);
      return;
    }
    
    // Subscribe to real-time updates on the user profile
    const unsubscribe = subscribeToData(`users/${user.uid}`, (data) => {
      if (data) {
        // Use function updater to avoid dependency on profile
        setProfile(prevProfile => ({
          ...prevProfile,
          ...data,
          email: user?.email || ''
        }));
      }
      setLoading(false);
    });
    
    // Clean up subscription on component unmount
    return () => unsubscribe();
  }, [user]); // Remove profile from dependencies

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.uid) {
      setError('User not authenticated');
      return;
    }
    
    try {
      setError('');
      setSuccess('');
      setSaving(true);
      
      // Add timestamp for when profile was last updated
      const updatedProfile = {
        ...profile,
        lastUpdated: Date.now()
      };
      
      console.log('Updating profile at path:', `users/${user.uid}`);
      console.log('With data:', updatedProfile);
      
      // Update user profile in the database
      const result = await updateData(`users/${user.uid}`, updatedProfile);
      
      if (result.success) {
        setSuccess('Profile updated successfully!');
        setSnackbarOpen(true);
        
        // Refresh the profile in the auth context
        await refreshProfile();
      } else {
        setError('Failed to update profile');
        console.error('Update result:', result);
      }
    } catch (err) {
      setError('An error occurred while saving your profile');
      console.error('Profile update error:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  return (
    <Layout title="Profile">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon color="primary" /> User Profile
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your profile information and settings.
        </Typography>
      </Box>

      {/* Success snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={5000}
        onClose={handleSnackbarClose}
        message={success}
      />

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={isMobile ? 2 : 3}>
          {/* Profile Card */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  bgcolor: 'primary.main',
                  fontSize: '2rem',
                  margin: '0 auto 16px',
                }}
              >
                {profile.displayName ? profile.displayName[0].toUpperCase() : 'U'}
              </Avatar>
              
              <Typography variant="h5" gutterBottom>
                {profile.displayName || 'User'}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" paragraph sx={{ 
                wordBreak: 'break-word',
                whiteSpace: 'pre-wrap' 
              }}>
                {profile.bio || 'No bio available'}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ textAlign: 'left' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Email
                </Typography>
                <Typography variant="body2" gutterBottom sx={{ wordBreak: 'break-all' }}>
                  {profile.email || 'No email available'}
                </Typography>
                
                <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  Phone
                </Typography>
                <Typography variant="body2" gutterBottom>
                  {profile.phone || 'No phone number available'}
                </Typography>
                
                <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                  School
                </Typography>
                <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                  {profile.school || 'No school information available'}
                </Typography>

                {profile.lastUpdated && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      Last updated: {new Date(profile.lastUpdated).toLocaleString()}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Paper>
          </Grid>
          
          {/* Edit Profile Form */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <EditIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Edit Profile
                </Typography>
              </Box>
              
              {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
              {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
              
              <Box component="form" onSubmit={handleSubmit}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Display Name"
                      name="displayName"
                      value={profile.displayName || ''}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Phone Number"
                      name="phone"
                      value={profile.phone || ''}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="School/Institution"
                      name="school"
                      value={profile.school || ''}
                      onChange={handleChange}
                      variant="outlined"
                    />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Bio"
                      name="bio"
                      multiline
                      rows={4}
                      value={profile.bio || ''}
                      onChange={handleChange}
                      variant="outlined"
                      placeholder="Tell us a bit about yourself..."
                    />
                  </Grid>
                </Grid>
                
                <Box sx={{ 
                  mt: 3, 
                  display: 'flex', 
                  justifyContent: 'flex-end',
                  flexDirection: isMobile ? 'column' : 'row',
                  gap: 2
                }}>
                  <Button 
                    type="submit" 
                    variant="contained" 
                    color="primary"
                    disabled={saving}
                    fullWidth={isMobile}
                    startIcon={<SaveIcon />}
                    sx={{ minWidth: 140 }}
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </Box>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Layout>
  );
};

export default UserProfile; 