import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Divider } from '@mui/material';
import Layout from './Layout';
import TimelineIcon from '@mui/icons-material/Timeline';

const Reports: React.FC = () => {
  // This would be replaced with real data from backend
  const mockData = {
    weeklyStats: [
      { day: 'Monday', focusRate: 85, studyHours: 4.2 },
      { day: 'Tuesday', focusRate: 78, studyHours: 3.5 },
      { day: 'Wednesday', focusRate: 90, studyHours: 5.1 },
      { day: 'Thursday', focusRate: 65, studyHours: 2.8 },
      { day: 'Friday', focusRate: 88, studyHours: 4.7 },
    ],
    distractions: [
      { type: 'Mobile Phone', count: 12, percentage: 42 },
      { type: 'Talking', count: 8, percentage: 28 },
      { type: 'Away from desk', count: 5, percentage: 17 },
      { type: 'Other', count: 4, percentage: 13 },
    ]
  };

  return (
    <Layout title="Reports">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon color="primary" /> Performance Reports
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View your study session statistics and performance metrics.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Weekly Focus Rate */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Weekly Focus Rate</Typography>
            <Divider sx={{ mb: 3 }}/>
            
            {/* This would be replaced with an actual chart component */}
            <Box sx={{ 
              height: 300, 
              bgcolor: '#f9f9f9', 
              borderRadius: 1, 
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Typography color="text.secondary">
                Chart visualization would appear here
              </Typography>
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                {mockData.weeklyStats.map((day) => (
                  <Grid item xs={12} md={2.4} key={day.day}>
                    <Card variant="outlined" sx={{ textAlign: 'center', py: 1 }}>
                      <Typography variant="body2" color="text.secondary">{day.day}</Typography>
                      <Typography variant="h6" sx={{ color: 'primary.main', fontWeight: 'bold' }}>
                        {day.focusRate}%
                      </Typography>
                      <Typography variant="caption">
                        {day.studyHours} hrs
                      </Typography>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </Paper>
        </Grid>

        {/* Distraction Analysis */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Distraction Analysis</Typography>
            <Divider sx={{ mb: 3 }}/>
            
            {/* Simple list of distractions */}
            {mockData.distractions.map((item, index) => (
              <Box 
                key={item.type}
                sx={{ 
                  mb: 2, 
                  pb: 2,
                  borderBottom: index !== mockData.distractions.length - 1 ? '1px solid' : 'none',
                  borderColor: 'divider'
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">{item.type}</Typography>
                  <Typography variant="body2" fontWeight="medium">{item.count} times</Typography>
                </Box>
                <Box 
                  sx={{ 
                    mt: 1,
                    height: 8,
                    bgcolor: 'grey.200',
                    borderRadius: 1,
                    position: 'relative'
                  }}
                >
                  <Box 
                    sx={{ 
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      height: '100%',
                      width: `${item.percentage}%`,
                      bgcolor: 'warning.main',
                      borderRadius: 1
                    }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">{item.percentage}% of distractions</Typography>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Monthly Summary */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Monthly Summary</Typography>
            <Divider sx={{ mb: 3 }}/>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>82%</Typography>
                  <Typography variant="body2" color="text.secondary">Average Focus Rate</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>68h</Typography>
                  <Typography variant="body2" color="text.secondary">Total Study Time</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>12</Typography>
                  <Typography variant="body2" color="text.secondary">Study Sessions</Typography>
                </Card>
              </Grid>
              <Grid item xs={12} md={3}>
                <Card sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'primary.main' }}>24</Typography>
                  <Typography variant="body2" color="text.secondary">Distractions</Typography>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Layout>
  );
};

export default Reports; 