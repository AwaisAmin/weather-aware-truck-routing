import { createTheme } from '@mui/material/styles'

// Map-specific colors per mode; MapLibre paint properties need plain color values.
export const MAP_COLORS = {
  light: {
    style: 'https://tiles.openfreemap.org/styles/positron',
    selectedRoute: '#1f5fbf',
    otherRoute: '#8a99a8',
    casing: '#ffffff',
  },
  dark: {
    style: 'https://tiles.openfreemap.org/styles/dark',
    selectedRoute: '#5b9bff',
    otherRoute: '#7c8896',
    casing: '#1a1d22',
  },
}

export function createAppTheme(mode) {
  const dark = mode === 'dark'
  return createTheme({
    palette: {
      mode,
      primary: { main: MAP_COLORS[mode].selectedRoute },
      background: dark ? { default: '#0f1216', paper: '#171b21' } : { default: '#f4f6f9', paper: '#ffffff' },
      divider: dark ? 'rgba(255,255,255,0.09)' : 'rgba(0,0,0,0.09)',
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      button: { textTransform: 'none', fontWeight: 600 },
    },
    components: {
      MuiAppBar: {
        styleOverrides: {
          root: dark
            ? {
                backgroundColor: '#171b21',
                backgroundImage: 'none',
                borderBottom: '1px solid rgba(255,255,255,0.09)',
              }
            : { backgroundImage: 'linear-gradient(90deg, #1f5fbf 0%, #2b73d9 100%)' },
        },
      },
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
      MuiCard: {
        styleOverrides: {
          root: {
            transition: 'border-color 150ms, box-shadow 150ms',
            '&:hover': { boxShadow: '0 2px 10px rgba(0,0,0,0.12)' },
          },
        },
      },
    },
  })
}
