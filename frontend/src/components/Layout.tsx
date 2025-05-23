import React, { useState, useEffect } from 'react';
import { Box, Toolbar, AppBar, IconButton, Typography, Container, useTheme, useMediaQuery } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SideNavigation from './SideNavigation';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const drawerExpandedWidth = 280;
const drawerCollapsedWidth = 72;

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  
  // Close mobile drawer when screen size changes to desktop
  useEffect(() => {
    if (!isSmallScreen && mobileOpen) {
      setMobileOpen(false);
    }
  }, [isSmallScreen, mobileOpen]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };
  
  // Calculate the drawer width based on screen size
  const sidebarWidth = isTablet ? drawerCollapsedWidth : drawerExpandedWidth;

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      {/* Sidebar navigation */}
      <SideNavigation 
        mobileOpen={mobileOpen} 
        onMobileClose={handleDrawerToggle} 
      />

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { 
            xs: '100%',
            sm: `calc(100% - ${drawerCollapsedWidth}px)`,
            md: `calc(100% - ${sidebarWidth}px)`
          },
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: 'background.default',
          transition: theme => theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        {/* Mobile app bar */}
        <AppBar
          position="fixed"
          elevation={0}
          sx={{
            display: { xs: 'flex', sm: 'none' },
            width: { sm: `calc(100% - ${drawerCollapsedWidth}px)` },
            ml: { sm: `${drawerCollapsedWidth}px` },
            bgcolor: 'background.paper',
            color: 'text.primary',
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" noWrap component="div">
              {title || 'EDUGuard'}
            </Typography>
          </Toolbar>
        </AppBar>
        
        {/* Toolbar spacer for mobile only */}
        <Box sx={{ display: { xs: 'block', sm: 'none' } }}>
          <Toolbar />
        </Box>

        {/* Page content with scrolling */}
        <Box sx={{ 
          flexGrow: 1, 
          p: { xs: 2, sm: 3, md: 4 }, 
          overflow: 'auto', // Enable scrolling for content
          width: '100%'
        }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout; 