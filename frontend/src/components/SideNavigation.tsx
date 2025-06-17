// SideNavigation.tsx (Responsive Styling Preserved, Improved Layout)
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  Toolbar, Divider, Avatar, Typography, IconButton, Tooltip,
  useMediaQuery, useTheme
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PersonIcon from '@mui/icons-material/Person';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import AssessmentIcon from '@mui/icons-material/Assessment';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import { useAuth } from '../contexts/AuthContext';
import Logo from '../assets/logo.png';

const drawerExpandedWidth = 280;
const drawerCollapsedWidth = 72;

interface SideNavigationProps {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
}

const SideNavigation: React.FC<SideNavigationProps> = ({
  mobileOpen = false,
  onMobileClose = () => {},
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  const [isCollapsed, setIsCollapsed] = useState<boolean>(isTablet);

  useEffect(() => {
    setIsCollapsed(isTablet);
  }, [isTablet]);

  const handleNavigation = (path: string) => {
    navigate(path);
    onMobileClose();
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Failed to log out:', error);
    }
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Reports', icon: <AssessmentIcon />, path: '/reports' },
    { text: 'Profile', icon: <PersonIcon />, path: '/profile' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ];

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ justifyContent: isCollapsed ? 'center' : 'space-between', px: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <img src={Logo} alt="Logo" style={{ width: isCollapsed ? 32 : 40, height: 'auto' }} />
          {!isCollapsed && <Typography variant="h6" sx={{ ml: 2, fontWeight: 'bold' }}>EDUGuard</Typography>}
        </Box>
        <IconButton onClick={toggleCollapse} sx={{ display: { xs: 'none', sm: 'block' } }}>
          {isCollapsed ? <MenuIcon /> : <ChevronLeftIcon />}
        </IconButton>
      </Toolbar>

      {!isCollapsed && user && (
        <Box sx={{ px: 2, py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>{user.email?.[0].toUpperCase()}</Avatar>
            <Box>
              <Typography>{user.email?.split('@')[0]}</Typography>
              <Typography variant="caption" color="text.secondary">Student</Typography>
            </Box>
          </Box>
        </Box>
      )}

      <List>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem disablePadding key={item.text}>
              <Tooltip title={isCollapsed ? item.text : ''} placement="right">
                <ListItemButton
                  selected={isActive}
                  onClick={() => handleNavigation(item.path)}
                  sx={{ justifyContent: isCollapsed ? 'center' : 'flex-start', px: 2 }}
                >
                  <ListItemIcon sx={{ minWidth: isCollapsed ? 'auto' : 40 }}>
                    {item.icon}
                  </ListItemIcon>
                  {!isCollapsed && <ListItemText primary={item.text} />}
                </ListItemButton>
              </Tooltip>
            </ListItem>
          );
        })}
      </List>

      <Box sx={{ mt: 'auto', mb: 2 }}>
        <ListItem disablePadding>
          <Tooltip title={isCollapsed ? 'Logout' : ''} placement="right">
            <ListItemButton
              onClick={handleLogout}
              sx={{ justifyContent: isCollapsed ? 'center' : 'flex-start', px: 2 }}
            >
              <ListItemIcon sx={{ minWidth: isCollapsed ? 'auto' : 40 }}>
                <LogoutIcon color="error" />
              </ListItemIcon>
              {!isCollapsed && <ListItemText primary="Logout" primaryTypographyProps={{ color: 'error.main' }} />}
            </ListItemButton>
          </Tooltip>
        </ListItem>
      </Box>
    </Box>
  );

  return (
    <>
      {/* Mobile */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            width: drawerExpandedWidth,
          },
        }}
      >
        {drawer}
      </Drawer>

      {/* Desktop/Tablet */}
      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: 'none', sm: 'block' },
          width: isCollapsed ? drawerCollapsedWidth : drawerExpandedWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: isCollapsed ? drawerCollapsedWidth : drawerExpandedWidth,
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.standard,
            }),
            overflowX: 'hidden',
            backgroundColor: theme.palette.background.paper,
            borderRight: '1px solid #e0e0e0'
          },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default SideNavigation;