import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  ToggleButtonGroup,
  ToggleButton,
  CircularProgress,
  Tabs,
  Tab,
  Alert
} from '@mui/material';
import Layout from './Layout';

// Material UI Icons
import TimelineIcon from '@mui/icons-material/Timeline';
import AccessibilityNewIcon from '@mui/icons-material/AccessibilityNew';
import SentimentDissatisfiedIcon from '@mui/icons-material/SentimentDissatisfied';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import OpacityIcon from '@mui/icons-material/Opacity';
import DateRangeIcon from '@mui/icons-material/DateRange';
import ViewWeekIcon from '@mui/icons-material/ViewWeek';
import ViewDayIcon from '@mui/icons-material/ViewDay';

// Recharts
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';

// Services
import { reportsService } from '../services/api';

// Timeframe selector component
const TimeframeSelector: React.FC<{
  timeframe: string;
  onTimeframeChange: (newTimeframe: string) => void;
}> = ({ timeframe, onTimeframeChange }) => {
  return (
    <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
      <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
        Timeframe:
      </Typography>
      <ToggleButtonGroup
        value={timeframe}
        exclusive
        onChange={(e, newValue) => {
          if (newValue) onTimeframeChange(newValue);
        }}
        size="small"
        aria-label="timeframe selection"
      >
        <ToggleButton value="daily" aria-label="daily">
          <ViewDayIcon sx={{ mr: 0.5, fontSize: '1rem' }} />
          Daily
        </ToggleButton>
        <ToggleButton value="weekly" aria-label="weekly">
          <ViewWeekIcon sx={{ mr: 0.5, fontSize: '1rem' }} />
          Weekly
        </ToggleButton>
        <ToggleButton value="monthly" aria-label="monthly">
          <DateRangeIcon sx={{ mr: 0.5, fontSize: '1rem' }} />
          Monthly
        </ToggleButton>
      </ToggleButtonGroup>
    </Box>
  );
};

// Main Reports component
const Reports: React.FC = () => {
  // State for timeframe selection
  const [timeframe, setTimeframe] = useState<string>('daily');
  
  // State for tab selection
  const [tabIndex, setTabIndex] = useState<number>(0);
  
  // Loading states
  const [loading, setLoading] = useState<{
    posture: boolean;
    stress: boolean;
    cvs: boolean;
    hydration: boolean;
    summary: boolean;
  }>({
    posture: false,
    stress: false,
    cvs: false,
    hydration: false,
    summary: false
  });
  
  // Error states
  const [error, setError] = useState<{
    posture: string | null;
    stress: string | null;
    cvs: string | null;
    hydration: string | null;
    summary: string | null;
  }>({
    posture: null,
    stress: null,
    cvs: null,
    hydration: null,
    summary: null
  });
  
  // Data states
  const [postureData, setPostureData] = useState<any>(null);
  const [stressData, setStressData] = useState<any>(null);
  const [cvsData, setCvsData] = useState<any>(null);
  const [hydrationData, setHydrationData] = useState<any>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  
  // Handle timeframe change
  const handleTimeframeChange = (newTimeframe: string) => {
    setTimeframe(newTimeframe);
  };
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };
  
  // Fetch data functions
  const fetchPostureData = async () => {
    setLoading(prev => ({ ...prev, posture: true }));
    setError(prev => ({ ...prev, posture: null }));
    
    try {
      const response = await reportsService.getPostureHistory(timeframe as any);
      if (response.status === 'success') {
        setPostureData(response.data);
      } else {
        setError(prev => ({ ...prev, posture: response.message || 'Failed to load posture data' }));
      }
    } catch (error) {
      console.error('Error fetching posture data:', error);
      setError(prev => ({ ...prev, posture: 'An error occurred while fetching posture data' }));
    } finally {
      setLoading(prev => ({ ...prev, posture: false }));
    }
  };
  
  const fetchStressData = async () => {
    setLoading(prev => ({ ...prev, stress: true }));
    setError(prev => ({ ...prev, stress: null }));
    
    try {
      const response = await reportsService.getStressHistory(timeframe as any);
      if (response.status === 'success') {
        setStressData(response.data);
      } else {
        setError(prev => ({ ...prev, stress: response.message || 'Failed to load stress data' }));
      }
    } catch (error) {
      console.error('Error fetching stress data:', error);
      setError(prev => ({ ...prev, stress: 'An error occurred while fetching stress data' }));
    } finally {
      setLoading(prev => ({ ...prev, stress: false }));
    }
  };
  
  const fetchCvsData = async () => {
    setLoading(prev => ({ ...prev, cvs: true }));
    setError(prev => ({ ...prev, cvs: null }));
    
    try {
      const response = await reportsService.getCVSHistory(timeframe as any);
      if (response.status === 'success') {
        setCvsData(response.data);
      } else {
        setError(prev => ({ ...prev, cvs: response.message || 'Failed to load eye strain data' }));
      }
    } catch (error) {
      console.error('Error fetching CVS data:', error);
      setError(prev => ({ ...prev, cvs: 'An error occurred while fetching eye strain data' }));
    } finally {
      setLoading(prev => ({ ...prev, cvs: false }));
    }
  };
  
  const fetchHydrationData = async () => {
    setLoading(prev => ({ ...prev, hydration: true }));
    setError(prev => ({ ...prev, hydration: null }));
    
    try {
      const response = await reportsService.getHydrationHistory(timeframe as any);
      if (response.status === 'success') {
        setHydrationData(response.data);
      } else {
        setError(prev => ({ ...prev, hydration: response.message || 'Failed to load hydration data' }));
      }
    } catch (error) {
      console.error('Error fetching hydration data:', error);
      setError(prev => ({ ...prev, hydration: 'An error occurred while fetching hydration data' }));
    } finally {
      setLoading(prev => ({ ...prev, hydration: false }));
    }
  };
  
  const fetchSummaryData = async () => {
    setLoading(prev => ({ ...prev, summary: true }));
    setError(prev => ({ ...prev, summary: null }));
    
    try {
      const response = await reportsService.getSummaryData(timeframe as any);
      if (response.status === 'success') {
        setSummaryData(response.data);
      } else {
        setError(prev => ({ ...prev, summary: response.message || 'Failed to load summary data' }));
      }
    } catch (error) {
      console.error('Error fetching summary data:', error);
      setError(prev => ({ ...prev, summary: 'An error occurred while fetching summary data' }));
    } finally {
      setLoading(prev => ({ ...prev, summary: false }));
    }
  };
  
  // Effect to fetch data when timeframe changes or tab changes
  useEffect(() => {
    const fetchActiveTabData = () => {
      switch (tabIndex) {
        case 0: // Summary tab
          fetchSummaryData();
          break;
        case 1: // Posture tab
          fetchPostureData();
          break;
        case 2: // Stress tab
          fetchStressData();
          break;
        case 3: // Eye Strain tab
          fetchCvsData();
          break;
        case 4: // Hydration tab
          fetchHydrationData();
          break;
        default:
          break;
      }
    };
    
    fetchActiveTabData();
  }, [timeframe, tabIndex]);
  
  // Colors for charts
  const COLORS = {
    posture: {
      good: '#4caf50',
      bad: '#f44336'
    },
    stress: {
      low: '#4caf50',
      medium: '#ff9800',
      high: '#f44336'
    },
    cvs: {
      normal: '#4caf50',
      low: '#ff9800',
      high: '#f44336'
    },
    hydration: {
      normal: '#4caf50',
      dry: '#f44336'
    }
  };
  
  // Function to check if data is empty
  const isDataEmpty = (data: any) => {
    if (!data) return true;
    
    // If it's summary data, check monitoring durations
    if (data.posture && data.stress && data.cvs && data.hydration) {
      return data.posture.monitoring_duration === 0 && 
             data.stress.monitoring_duration === 0 && 
             data.cvs.monitoring_duration === 0 && 
             data.hydration.monitoring_duration === 0;
    }
    
    // Check if labels array exists and is empty
    if (!data.labels || !Array.isArray(data.labels) || data.labels.length === 0) return true;
    
    // For posture data
    if (data.good_posture_percentage && data.good_posture_percentage.length === 0) return true;
    
    // For stress data
    if (data.low_stress_percentage && data.low_stress_percentage.length === 0) return true;
    
    // For CVS data
    if (data.normal_blink_percentage && data.normal_blink_percentage.length === 0) return true;
    
    // For hydration data
    if (data.normal_lips_percentage && data.normal_lips_percentage.length === 0) return true;
    
    return false;
  };
  
  // Empty state component
  const EmptyDataState = ({ monitoringType }: { monitoringType: string }) => {
    return (
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center', 
        p: 4, 
        textAlign: 'center',
        minHeight: '300px',
        backgroundColor: 'rgba(0,0,0,0.02)',
        borderRadius: 2
      }}>
        <TimelineIcon sx={{ fontSize: 60, color: 'text.secondary', opacity: 0.3, mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No {monitoringType} Data Available
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 500 }}>
          There is no monitoring data available for the selected timeframe. Please ensure you have 
          run the {monitoringType.toLowerCase()} monitoring for some time, or try a different timeframe.
        </Typography>
        <Alert severity="info" sx={{ mt: 2, maxWidth: 500 }}>
          Data will appear here once you have used the {monitoringType.toLowerCase()} monitoring features.
        </Alert>
      </Box>
    );
  };
  
  // Component for summary section
  const renderSummarySection = () => {
    if (loading.summary) {
      return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }
    
    if (error.summary) {
      return <Alert severity="error" sx={{ m: 2 }}>{error.summary}</Alert>;
    }
    
    if (!summaryData) {
      return <EmptyDataState monitoringType="Summary" />;
    }
    
    return (
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', py: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
              <AccessibilityNewIcon color="primary" sx={{ fontSize: '2rem' }} />
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              {summaryData.posture?.good_posture_percentage || 0}%
            </Typography>
            <Typography variant="body2" color="text.secondary">Good Posture</Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              {summaryData.posture?.monitoring_duration || 0} min monitored
            </Typography>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', py: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
              <SentimentDissatisfiedIcon color="secondary" sx={{ fontSize: '2rem' }} />
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'secondary.main' }}>
              {summaryData.stress?.low_stress_percentage || 0}%
            </Typography>
            <Typography variant="body2" color="text.secondary">Low Stress</Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              {summaryData.stress?.monitoring_duration || 0} min monitored
            </Typography>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', py: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
              <VisibilityOffIcon color="info" sx={{ fontSize: '2rem' }} />
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main' }}>
              {summaryData.cvs?.normal_blink_percentage || 0}%
            </Typography>
            <Typography variant="body2" color="text.secondary">Normal Blink Rate</Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              {summaryData.cvs?.monitoring_duration || 0} min monitored
            </Typography>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card sx={{ textAlign: 'center', py: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 1 }}>
              <OpacityIcon color="warning" sx={{ fontSize: '2rem' }} />
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
              {summaryData.hydration?.normal_lips_percentage || 0}%
            </Typography>
            <Typography variant="body2" color="text.secondary">Normal Hydration</Typography>
            <Typography variant="caption" display="block" sx={{ mt: 1 }}>
              {summaryData.hydration?.monitoring_duration || 0} min monitored
            </Typography>
          </Card>
        </Grid>
        
        {/* Overall Health Score */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Overall Health Score</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 2 }}>
                <Box
                  sx={{
                    position: 'relative',
                    display: 'inline-flex'
                  }}
                >
                  <CircularProgress
                    variant="determinate"
                    value={summaryData.overall_health_score || 0}
                    size={120}
                    thickness={5}
                    sx={{
                      color: summaryData.overall_health_score > 75 
                        ? 'success.main' 
                        : summaryData.overall_health_score > 50 
                          ? 'warning.main' 
                          : 'error.main'
                    }}
                  />
                  <Box
                    sx={{
                      top: 0,
                      left: 0,
                      bottom: 0,
                      right: 0,
                      position: 'absolute',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography
                      variant="h4"
                      component="div"
                      color="text.primary"
                    >
                      {`${Math.round(summaryData.overall_health_score || 0)}%`}
                    </Typography>
                  </Box>
                </Box>
              </Box>
              <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
                This score represents your overall health based on posture, stress, eye strain, and hydration monitoring.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };
  
  // Component for posture section
  const renderPostureSection = () => {
    if (loading.posture) {
      return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }
    
    if (error.posture) {
      return <Alert severity="error" sx={{ m: 2 }}>{error.posture}</Alert>;
    }
    
    if (!postureData || isDataEmpty(postureData)) {
      return <EmptyDataState monitoringType="Posture" />;
    }
    
    // Transform data for chart
    const chartData = postureData.labels.map((label: string, index: number) => ({
      name: label,
      goodPosture: postureData.good_posture_percentage[index] || 0,
      badPosture: postureData.bad_posture_percentage[index] || 0
    }));
    
    return (
      <Grid container spacing={3}>
        {/* Posture Trend Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Posture Trend</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {timeframe === 'daily' ? 'Hourly' : timeframe === 'weekly' ? 'Daily' : 'Monthly'} breakdown of your posture
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={chartData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis unit="%" />
                    <Tooltip formatter={(value) => [`${value}%`, '']} />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="goodPosture" 
                      name="Good Posture"
                      stackId="1"
                      stroke={COLORS.posture.good} 
                      fill={COLORS.posture.good} 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="badPosture" 
                      name="Bad Posture"
                      stackId="1"
                      stroke={COLORS.posture.bad} 
                      fill={COLORS.posture.bad} 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Posture Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Posture Distribution</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Good Posture', value: postureData.good_posture_percentage ? 
                          postureData.good_posture_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          postureData.good_posture_percentage.length : 0 
                        },
                        { name: 'Bad Posture', value: postureData.bad_posture_percentage ? 
                          postureData.bad_posture_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          postureData.bad_posture_percentage.length : 0 
                        }
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell key="good" fill={COLORS.posture.good} />
                      <Cell key="bad" fill={COLORS.posture.bad} />
                    </Pie>
                    <Tooltip formatter={(value: any) => [
                      typeof value === 'number' ? `${value.toFixed(1)}%` : `${value}%`, 
                      ''
                    ]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Posture Stats */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Posture Statistics</Typography>
              <Box sx={{ p: 2 }}>
                <Typography variant="body1" gutterBottom>
                  <strong>Average Good Posture:</strong> {postureData.good_posture_percentage ? 
                    (postureData.good_posture_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     postureData.good_posture_percentage.length).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Average Bad Posture:</strong> {postureData.bad_posture_percentage ? 
                    (postureData.bad_posture_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     postureData.bad_posture_percentage.length).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Highest Good Posture:</strong> {postureData.good_posture_percentage ? 
                    Math.max(...postureData.good_posture_percentage).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Lowest Good Posture:</strong> {postureData.good_posture_percentage ? 
                    Math.min(...postureData.good_posture_percentage).toFixed(1) : 0}%
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommendations:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {postureData.good_posture_percentage && 
                    (postureData.good_posture_percentage.reduce((a: number, b: number) => a + b, 0) / 
                    postureData.good_posture_percentage.length) < 70 ? (
                      "Consider improving your sitting posture by keeping your back straight, shoulders relaxed, and screen at eye level. Take regular breaks to stretch."
                    ) : (
                      "Great job maintaining good posture! Continue your good habits and remember to take regular breaks to stretch and move around."
                    )}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };
  
  // Component for stress section
  const renderStressSection = () => {
    if (loading.stress) {
      return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }
    
    if (error.stress) {
      return <Alert severity="error" sx={{ m: 2 }}>{error.stress}</Alert>;
    }
    
    if (!stressData || isDataEmpty(stressData)) {
      return <EmptyDataState monitoringType="Stress" />;
    }
    
    // Transform data for chart
    const chartData = stressData.labels.map((label: string, index: number) => ({
      name: label,
      lowStress: stressData.low_stress_percentage[index] || 0,
      mediumStress: stressData.medium_stress_percentage[index] || 0,
      highStress: stressData.high_stress_percentage[index] || 0
    }));
    
    return (
      <Grid container spacing={3}>
        {/* Stress Level Trend Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Stress Level Trend</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {timeframe === 'daily' ? 'Hourly' : timeframe === 'weekly' ? 'Daily' : 'Monthly'} breakdown of your stress levels
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis unit="%" />
                    <Tooltip formatter={(value) => [`${value}%`, '']} />
                    <Legend />
                    <Bar 
                      dataKey="lowStress" 
                      name="Low Stress"
                      stackId="a"
                      fill={COLORS.stress.low} 
                    />
                    <Bar 
                      dataKey="mediumStress" 
                      name="Medium Stress"
                      stackId="a"
                      fill={COLORS.stress.medium} 
                    />
                    <Bar 
                      dataKey="highStress" 
                      name="High Stress"
                      stackId="a"
                      fill={COLORS.stress.high} 
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Stress Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Stress Distribution</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Low Stress', value: stressData.low_stress_percentage ? 
                          stressData.low_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          stressData.low_stress_percentage.length : 0 
                        },
                        { name: 'Medium Stress', value: stressData.medium_stress_percentage ? 
                          stressData.medium_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          stressData.medium_stress_percentage.length : 0 
                        },
                        { name: 'High Stress', value: stressData.high_stress_percentage ? 
                          stressData.high_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          stressData.high_stress_percentage.length : 0 
                        }
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell key="low" fill={COLORS.stress.low} />
                      <Cell key="medium" fill={COLORS.stress.medium} />
                      <Cell key="high" fill={COLORS.stress.high} />
                    </Pie>
                    <Tooltip formatter={(value: any) => [
                      typeof value === 'number' ? `${value.toFixed(1)}%` : `${value}%`, 
                      ''
                    ]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Stress Stats */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Stress Statistics</Typography>
              <Box sx={{ p: 2 }}>
                <Typography variant="body1" gutterBottom>
                  <strong>Average Low Stress:</strong> {stressData.low_stress_percentage ? 
                    (stressData.low_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     stressData.low_stress_percentage.length).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Average Medium Stress:</strong> {stressData.medium_stress_percentage ? 
                    (stressData.medium_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     stressData.medium_stress_percentage.length).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Average High Stress:</strong> {stressData.high_stress_percentage ? 
                    (stressData.high_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     stressData.high_stress_percentage.length).toFixed(1) : 0}%
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommendations:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stressData.high_stress_percentage && 
                    (stressData.high_stress_percentage.reduce((a: number, b: number) => a + b, 0) / 
                    stressData.high_stress_percentage.length) > 30 ? (
                      "Your stress levels are elevated. Consider taking breaks, practicing deep breathing exercises, or meditation to reduce stress."
                    ) : (
                      "Your stress levels are generally low. Continue your good stress management practices and maintain a healthy work-life balance."
                    )}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };
  
  // Component for CVS (eye strain) section
  const renderCVSSection = () => {
    if (loading.cvs) {
      return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }
    
    if (error.cvs) {
      return <Alert severity="error" sx={{ m: 2 }}>{error.cvs}</Alert>;
    }
    
    if (!cvsData || isDataEmpty(cvsData)) {
      return <EmptyDataState monitoringType="Eye Strain" />;
    }
    
    // Transform data for chart
    const chartData = cvsData.labels.map((label: string, index: number) => ({
      name: label,
      normalBlink: cvsData.normal_blink_percentage[index] || 0,
      lowBlink: cvsData.low_blink_percentage[index] || 0,
      highBlink: cvsData.high_blink_percentage[index] || 0,
      avgBlinkCount: cvsData.avg_blink_count[index] || 0
    }));
    
    return (
      <Grid container spacing={3}>
        {/* Blink Rate Trend Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Blink Rate Trend</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {timeframe === 'daily' ? 'Hourly' : timeframe === 'weekly' ? 'Daily' : 'Monthly'} breakdown of your blink patterns
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis yAxisId="left" unit="%" />
                    <YAxis yAxisId="right" orientation="right" domain={[0, 30]} />
                    <Tooltip formatter={(value, name) => [
                      name === 'avgBlinkCount' ? `${value} blinks/min` : `${value}%`,
                      name === 'avgBlinkCount' ? 'Average Blink Count' : name
                    ]} />
                    <Legend />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="normalBlink" 
                      name="Normal Blink Rate"
                      stroke={COLORS.cvs.normal} 
                      activeDot={{ r: 8 }} 
                    />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="lowBlink" 
                      name="Low Blink Rate"
                      stroke={COLORS.cvs.low} 
                    />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="highBlink" 
                      name="High Blink Rate"
                      stroke={COLORS.cvs.high} 
                    />
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="avgBlinkCount" 
                      name="Average Blink Count"
                      stroke="#8884d8" 
                      strokeDasharray="3 3"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Blink Rate Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Blink Rate Distribution</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Normal Blink Rate', value: cvsData.normal_blink_percentage ? 
                          cvsData.normal_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          cvsData.normal_blink_percentage.length : 0 
                        },
                        { name: 'Low Blink Rate', value: cvsData.low_blink_percentage ? 
                          cvsData.low_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          cvsData.low_blink_percentage.length : 0 
                        },
                        { name: 'High Blink Rate', value: cvsData.high_blink_percentage ? 
                          cvsData.high_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                          cvsData.high_blink_percentage.length : 0 
                        }
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell key="normal" fill={COLORS.cvs.normal} />
                      <Cell key="low" fill={COLORS.cvs.low} />
                      <Cell key="high" fill={COLORS.cvs.high} />
                    </Pie>
                    <Tooltip formatter={(value: any) => [
                      typeof value === 'number' ? `${value.toFixed(1)}%` : `${value}%`, 
                      ''
                    ]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Eye Strain Stats */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Eye Strain Statistics</Typography>
              <Box sx={{ p: 2 }}>
                <Typography variant="body1" gutterBottom>
                  <strong>Average Blink Count:</strong> {cvsData.avg_blink_count ? 
                    (cvsData.avg_blink_count.reduce((a: number, b: number) => a + b, 0) / 
                     cvsData.avg_blink_count.length).toFixed(1) : 0} blinks/min
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Normal Blink Rate:</strong> {cvsData.normal_blink_percentage ? 
                    (cvsData.normal_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     cvsData.normal_blink_percentage.length).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Low Blink Rate:</strong> {cvsData.low_blink_percentage ? 
                    (cvsData.low_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     cvsData.low_blink_percentage.length).toFixed(1) : 0}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>High Blink Rate:</strong> {cvsData.high_blink_percentage ? 
                    (cvsData.high_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                     cvsData.high_blink_percentage.length).toFixed(1) : 0}%
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommendations:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {cvsData.low_blink_percentage && 
                    (cvsData.low_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                    cvsData.low_blink_percentage.length) > 30 ? (
                      "Your blink rate is lower than recommended. Remember to blink regularly when using screens to prevent dry eyes. Consider using the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds."
                    ) : cvsData.high_blink_percentage && 
                    (cvsData.high_blink_percentage.reduce((a: number, b: number) => a + b, 0) / 
                    cvsData.high_blink_percentage.length) > 30 ? (
                      "Your blink rate is higher than normal, indicating possible eye fatigue. Consider reducing screen time and ensuring proper lighting conditions."
                    ) : (
                      "Your blink rate is generally normal. Continue taking regular breaks from screen use to maintain good eye health."
                    )}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };
  
  // Component for hydration section
  const renderHydrationSection = () => {
    if (loading.hydration) {
      return <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}><CircularProgress /></Box>;
    }
    
    if (error.hydration) {
      return <Alert severity="error" sx={{ m: 2 }}>{error.hydration}</Alert>;
    }
    
    if (!hydrationData || isDataEmpty(hydrationData)) {
      return <EmptyDataState monitoringType="Hydration" />;
    }
    
    // Ensure we have the required data arrays
    const normalLipsData = hydrationData.normal_lips_percentage || [];
    const dryLipsData = hydrationData.dry_lips_percentage || [];
    const dryScoreData = hydrationData.avg_dryness_score || [];
    const labels = hydrationData.labels || [];
    
    // Log data for debugging
    console.log('Hydration data:', {
      labels: labels.length,
      normalLips: normalLipsData.length,
      dryLips: dryLipsData.length,
      dryScore: dryScoreData.length,
      isFallback: hydrationData.is_fallback_data,
      isSample: hydrationData.is_sample_data
    });
    
    // Check if we're using fallback data
    const usingFallbackData = hydrationData.is_fallback_data || hydrationData.is_sample_data;
    
    // Transform data for chart - ensure all arrays have equal length
    const maxLength = Math.max(labels.length, normalLipsData.length, dryLipsData.length, dryScoreData.length);
    
    const chartData = labels.map((label: string, index: number) => ({
      name: label,
      normalLips: index < normalLipsData.length ? normalLipsData[index] : 0,
      dryLips: index < dryLipsData.length ? dryLipsData[index] : 0,
      dryScore: index < dryScoreData.length ? dryScoreData[index] : 0
    }));
    
    // Calculate averages safely
    const getAverage = (arr: number[]) => {
      if (!arr || arr.length === 0) return 0;
      const sum = arr.reduce((total, val) => total + (isNaN(val) ? 0 : val), 0);
      return sum / arr.length;
    };
    
    const avgNormalLips = getAverage(normalLipsData);
    const avgDryLips = getAverage(dryLipsData);
    const avgDryScore = getAverage(dryScoreData);
    
    return (
      <Grid container spacing={3}>
        {usingFallbackData && (
          <Grid item xs={12}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Limited hydration data available. This visualization includes sample data points to help understand the metrics.
            </Alert>
          </Grid>
        )}
        
        {/* Hydration Trend Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Hydration Trend</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {timeframe === 'daily' ? 'Hourly' : timeframe === 'weekly' ? 'Daily' : 'Monthly'} breakdown of your hydration levels
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart
                    data={chartData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis yAxisId="left" unit="%" />
                    <YAxis yAxisId="right" orientation="right" domain={[0, 1]} />
                    <Tooltip formatter={(value: any, name: string) => {
                      if (name === 'dryScore') {
                        return [
                          typeof value === 'number' ? `${value.toFixed(2)}` : `${String(value)}`,
                          'Dryness Score'
                        ];
                      }
                      return [`${value}%`, name === 'normalLips' ? 'Normal Hydration' : 'Dry Lips'];
                    }} />
                    <Legend />
                    <Area 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="normalLips" 
                      name="Normal Hydration"
                      stackId="1"
                      stroke={COLORS.hydration.normal} 
                      fill={COLORS.hydration.normal} 
                    />
                    <Area 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="dryLips" 
                      name="Dry Lips"
                      stackId="1"
                      stroke={COLORS.hydration.dry} 
                      fill={COLORS.hydration.dry} 
                    />
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="dryScore" 
                      name="Dryness Score"
                      stroke="#8884d8" 
                      strokeDasharray="3 3"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Hydration Distribution Pie Chart */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Hydration Distribution</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Normal Hydration', value: avgNormalLips },
                        { name: 'Dry Lips', value: avgDryLips }
                      ]}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      <Cell key="normal" fill={COLORS.hydration.normal} />
                      <Cell key="dry" fill={COLORS.hydration.dry} />
                    </Pie>
                    <Tooltip formatter={(value: any) => [
                      typeof value === 'number' ? `${value.toFixed(1)}%` : `${value}%`, 
                      ''
                    ]} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Hydration Stats */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Hydration Statistics</Typography>
              <Box sx={{ p: 2 }}>
                <Typography variant="body1" gutterBottom>
                  <strong>Average Dryness Score:</strong> {avgDryScore.toFixed(2)}
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Normal Hydration:</strong> {avgNormalLips.toFixed(1)}%
                </Typography>
                <Typography variant="body1" gutterBottom>
                  <strong>Dry Lips:</strong> {avgDryLips.toFixed(1)}%
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommendations:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {avgDryLips > 30 ? (
                      "Your hydration levels appear to be low. Remember to drink water regularly throughout the day. Aim for at least 8 glasses of water daily."
                    ) : (
                      "Your hydration levels are good. Continue drinking water regularly to maintain proper hydration."
                    )}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <Layout title="Reports">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon color="primary" /> Health Monitoring Reports
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View detailed reports and trends for your health monitoring metrics.
        </Typography>
      </Box>
      
      {/* Timeframe selector */}
      <TimeframeSelector timeframe={timeframe} onTimeframeChange={handleTimeframeChange} />
      
      {/* Tab navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={tabIndex} 
          onChange={handleTabChange} 
          aria-label="health monitoring tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab 
            label="Summary" 
            icon={<TimelineIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Posture" 
            icon={<AccessibilityNewIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Stress" 
            icon={<SentimentDissatisfiedIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Eye Strain" 
            icon={<VisibilityOffIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Hydration" 
            icon={<OpacityIcon />} 
            iconPosition="start"
          />
        </Tabs>
      </Box>
      
      {/* Tab content */}
      <Box sx={{ mt: 3 }}>
        {tabIndex === 0 && renderSummarySection()}
        {tabIndex === 1 && renderPostureSection()}
        {tabIndex === 2 && renderStressSection()}
        {tabIndex === 3 && renderCVSSection()}
        {tabIndex === 4 && renderHydrationSection()}
      </Box>
    </Layout>
  );
};

export default Reports; 