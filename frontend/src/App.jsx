import { useEffect, useState } from 'react'
import { AppBar, Box, Chip, Toolbar, Typography } from '@mui/material'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import { apiGet } from './api.js'

export default function App() {
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    const controller = new AbortController()
    apiGet('/api/health/', { signal: controller.signal })
      .then(() => setApiStatus('online'))
      .catch((error) => {
        if (error.name !== 'AbortError') setApiStatus('offline')
      })
    return () => controller.abort()
  }, [])

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar sx={{ gap: 1.5 }}>
          <LocalShippingIcon />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Weather-Aware Truck Routing
          </Typography>
          <Chip
            size="small"
            label={`API ${apiStatus}`}
            color={apiStatus === 'online' ? 'success' : apiStatus === 'offline' ? 'error' : 'default'}
            sx={{ color: 'common.white' }}
          />
        </Toolbar>
      </AppBar>
    </Box>
  )
}
