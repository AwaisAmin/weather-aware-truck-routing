import { useCallback, useMemo } from 'react'
import { Alert, AlertTitle, Box, Divider, Stack, Typography } from '@mui/material'
import RouteCard from './RouteCard.jsx'
import CheckpointList from './CheckpointList.jsx'

export default function RouteResults({ plan, selectedRouteId, onSelectRoute, focus, onFocus }) {
  const ranked = useMemo(() => [...plan.routes].sort((a, b) => a.rank - b.rank), [plan])
  const selected = plan.routes.find((route) => route.id === selectedRouteId)
  const focusCheckpoint = useCallback(
    (index) => onFocus({ routeId: selectedRouteId, index, fromList: true }),
    [onFocus, selectedRouteId],
  )

  return (
    <Stack spacing={2}>
      <Alert severity="success" variant="outlined">
        <AlertTitle sx={{ mb: 0.25 }}>Take route {plan.recommended_route_id}</AlertTitle>
        {plan.recommendation_reason.replace(/^Recommended: (\w)/, (_, first) => first.toUpperCase())}
      </Alert>

      <Stack spacing={1.25}>
        {ranked.map((route) => (
          <RouteCard
            key={route.id}
            route={route}
            selected={route.id === selectedRouteId}
            onSelect={() => onSelectRoute(route.id)}
          />
        ))}
      </Stack>

      {selected && (
        <Box>
          <Divider sx={{ mb: 1.5 }} />
          <Stack direction="row" sx={{ alignItems: 'baseline', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="subtitle2">Route {selected.id} checkpoints</Typography>
            <Typography variant="caption" color="text.secondary">
              every {plan.interval_miles} mi · your local time
            </Typography>
          </Stack>
          <CheckpointList
            route={selected}
            focusedIndex={focus?.routeId === selected.id ? focus.index : null}
            onFocus={focusCheckpoint}
          />
        </Box>
      )}
    </Stack>
  )
}
