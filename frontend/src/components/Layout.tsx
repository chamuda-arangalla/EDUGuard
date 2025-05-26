import React, { useState, useEffect } from 'react';
import {
  Box,
  Toolbar,
  AppBar,
  IconButton,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
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

  useEffect(() => {
    if (!isSmallScreen && mobileOpen) {
      setMobileOpen(false);
    }
  }, [isSmallScreen, mobileOpen]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const sidebarWidth = isTablet ? drawerCollapsedWidth : drawerExpandedWidth;

  return (
    <Box
      sx={{
        display: 'flex',
        height: '100vh',
        bgcolor: 'background.default',
        overflow: 'hidden',
      }}
    >
      {/* Sidebar navigation */}
      <Box
        sx={{
          width: {
            xs: 0,
            sm: `${drawerCollapsedWidth}px`,
            md: `${drawerExpandedWidth}px`,
          },
          height: '100vh',
          bgcolor: 'background.paper',
          position: 'fixed',
          zIndex: theme.zIndex.drawer,
          display: { xs: 'none', sm: 'block' },
        }}
      >
        <SideNavigation />
      </Box>

      {/* Mobile Sidebar */}
      {isSmallScreen && (
        <SideNavigation
          mobileOpen={mobileOpen}
          onMobileClose={handleDrawerToggle}
        />
      )}

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: '100%',
          height: '100vh',
          ml: {
            xs: 0,
            sm: `${drawerCollapsedWidth}px`,
            md: `${drawerExpandedWidth}px`,
          },
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* App Bar for Mobile */}
        <AppBar
          position="fixed"
          elevation={0}
          sx={{
            display: { xs: 'flex', sm: 'none' },
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

        {/* Spacer for mobile app bar */}
        <Box sx={{ display: { xs: 'block', sm: 'none' } }}>
          <Toolbar />
        </Box>

        {/* Content container */}
        <Box
          sx={{
            flexGrow: 1,
            p: { xs: 1.5, sm: 2, md: 2.5 },
            overflow: 'auto',
            width: '100%',
            height: '100%',
            boxSizing: 'border-box',
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;
