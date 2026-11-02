import { useCallback, useRef, useState } from 'react'
import { Alert, AppBar, Box, Paper, Toolbar, Typography } from '@mui/material'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import { planTrip } from './api.js'
import TripForm from './components/TripForm.jsx'

const SIDEBAR_WIDTH = 400

export default function App() {
  const [plan, setPlan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const requestRef = useRef(null)

  const handlePlan = useCallback(async (payload) => {
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setLoading(true)
    setError(null)
    try {
      setPlan(await planTrip(payload, { signal: controller.signal }))
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message)
    } finally {
      if (requestRef.current === controller) setLoading(false)
    }
  }, [])

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar variant="dense" sx={{ gap: 1.5 }}>
          <LocalShippingIcon />
          <Typography variant="h6" component="h1" sx={{ fontWeight: 600, fontSize: { xs: 16, sm: 20 } }}>
            Weather-Aware Truck Routing
          </Typography>
        </Toolbar>
      </AppBar>

      <Box sx={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}>
        <Paper
          square
          elevation={0}
          sx={{
            width: { xs: '100%', md: SIDEBAR_WIDTH },
            flexShrink: 0,
            borderRight: { md: 1 },
            borderBottom: { xs: 1, md: 0 },
            borderColor: { xs: 'divider', md: 'divider' },
            overflowY: { md: 'auto' },
            p: 2,
          }}
        >
          <TripForm loading={loading} onSubmit={handlePlan} />
          {error && (
            <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}
          {plan && !loading && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Route {plan.recommended_route_id} — {plan.recommendation_reason}
            </Alert>
          )}
        </Paper>

        <Box sx={{ flex: 1, minHeight: { xs: 420, md: 0 }, bgcolor: 'grey.200' }} />
      </Box>
    </Box>
  )
}
