import React, { useState, useEffect } from 'react';
import { Box, Toolbar, AppBar, IconButton, Typography, useTheme, useMediaQuery } from '@mui/material';
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
    <Box sx={{ 
      display: 'flex', 
      height: '100vh', 
      overflow: 'hidden',
      bgcolor: 'background.default',
    }}>
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
          width: '100%',
          height: '100vh',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          ml: { 
            xs: 0,
            sm: `${drawerCollapsedWidth}px`,
            md: `${drawerExpandedWidth}px`
          },
          transition: 'none',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* Mobile app bar */}
        <AppBar
          position="fixed"
          elevation={0}
          sx={{
            display: { xs: 'flex', sm: 'none' },
            width: { xs: '100%', sm: `calc(100% - ${drawerCollapsedWidth}px)` },
            ml: { xs: 0, sm: `${drawerCollapsedWidth}px` },
            bgcolor: 'background.paper',
            color: 'text.primary',
            borderBottom: '1px solid',
            borderColor: 'divider',
            zIndex: theme.zIndex.drawer + 1,
          }}
        >
          <Toolbar sx={{ px: 2 }}>
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
          p: { xs: 1.5, sm: 2, md: 2.5 },
          overflow: 'auto',
          width: '100%',
          height: '100%',
          boxSizing: 'border-box',
        }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout; 