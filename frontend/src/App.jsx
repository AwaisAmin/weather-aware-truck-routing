import { Suspense, lazy, useCallback, useRef, useState } from 'react'
import { Alert, AppBar, Box, CircularProgress, Paper, Toolbar, Typography } from '@mui/material'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import { fetchHeatmap, planTrip } from './api.js'
import RouteResults from './components/RouteResults.jsx'
import TripForm from './components/TripForm.jsx'
import { downsample } from './utils/route.js'

// MapLibre is the largest dependency; load it in parallel so the form renders first.
const RouteMap = lazy(() => import('./components/RouteMap.jsx'))

const SIDEBAR_WIDTH = 400
// Keeps the heatmap request small; the corridor is ~40 miles wide, so detail is not needed.
const HEATMAP_POINTS_PER_ROUTE = 150
const EMPTY_HEATMAP = { data: null, loading: false, error: null }

export default function App() {
  const [plan, setPlan] = useState(null)
  const [selectedRouteId, setSelectedRouteId] = useState(null)
  // Checkpoint whose details are open: { routeId, index, fromList }.
  const [focus, setFocus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [heatmapState, setHeatmapState] = useState(EMPTY_HEATMAP)
  const requestRef = useRef(null)
  const heatmapRequestRef = useRef(null)

  const loadHeatmap = useCallback(async (forPlan) => {
    heatmapRequestRef.current?.abort()
    const controller = new AbortController()
    heatmapRequestRef.current = controller
    setHeatmapState({ data: null, loading: true, error: null })
    try {
      const data = await fetchHeatmap(
        {
          routes: forPlan.routes.map((route) => downsample(route.geometry, HEATMAP_POINTS_PER_ROUTE)),
          departure: forPlan.departure,
          load_lb: forPlan.load_lb,
        },
        { signal: controller.signal },
      )
      setHeatmapState({ data, loading: false, error: null })
    } catch (err) {
      if (err.name !== 'AbortError') setHeatmapState({ data: null, loading: false, error: err.message })
    }
  }, [])

  const handlePlan = useCallback(
    async (payload) => {
      requestRef.current?.abort()
      heatmapRequestRef.current?.abort()
      const controller = new AbortController()
      requestRef.current = controller
      setLoading(true)
      setError(null)
      try {
        const result = await planTrip(payload, { signal: controller.signal })
        setPlan(result)
        setSelectedRouteId(result.recommended_route_id)
        setFocus(null)
        // The heatmap loads after the routes so they appear as soon as possible.
        loadHeatmap(result)
      } catch (err) {
        if (err.name !== 'AbortError') setError(err.message)
      } finally {
        if (requestRef.current === controller) setLoading(false)
      }
    },
    [loadHeatmap],
  )

  const selectRoute = useCallback((routeId) => {
    setSelectedRouteId(routeId)
    setFocus(null)
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
            borderColor: 'divider',
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
          {plan && (
            <Box sx={{ mt: 2, opacity: loading ? 0.5 : 1, transition: 'opacity 200ms' }}>
              <RouteResults
                plan={plan}
                selectedRouteId={selectedRouteId}
                onSelectRoute={selectRoute}
                focus={focus}
                onFocus={setFocus}
              />
            </Box>
          )}
        </Paper>

        <Box sx={{ flex: 1, minHeight: { xs: 420, md: 0 }, bgcolor: 'grey.200' }}>
          <Suspense
            fallback={
              <Box sx={{ height: '100%', display: 'grid', placeItems: 'center' }}>
                <CircularProgress />
              </Box>
            }
          >
            <RouteMap
              plan={plan}
              selectedRouteId={selectedRouteId}
              onSelectRoute={selectRoute}
              focus={focus}
              onFocus={setFocus}
              heatmapState={heatmapState}
              onRetryHeatmap={() => plan && loadHeatmap(plan)}
            />
          </Suspense>
        </Box>
      </Box>
    </Box>
  )
}
