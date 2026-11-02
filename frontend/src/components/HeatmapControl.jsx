import { useEffect, useRef } from 'react'
import dayjs from 'dayjs'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControlLabel,
  IconButton,
  Paper,
  Slider,
  Stack,
  Switch,
  Typography,
} from '@mui/material'
import PlayArrowRoundedIcon from '@mui/icons-material/PlayArrowRounded'
import PauseRoundedIcon from '@mui/icons-material/PauseRounded'

// Ticks every 12 h; the current hour is shown in the caption below the slider.
const MARKS = [0, 12, 24, 36, 48].map((value) => ({ value }))
// Forecast hours advanced per second of playback.
const PLAYBACK_HOURS_PER_SECOND = 3

function truckStatus(truck, routeId) {
  if (!truck) return null
  if (truck.status === 'waiting') return `Route ${routeId}: not departed yet`
  if (truck.status === 'arrived') return `Route ${routeId}: arrived`
  return `Route ${routeId}: truck at mile ${Math.round(truck.mile)}`
}

export default function HeatmapControl({
  heatmap,
  loading,
  error,
  onRetry,
  hour,
  onHourChange,
  playing,
  onPlayingChange,
  visible,
  onVisibleChange,
  truck,
  routeId,
}) {
  const frameRef = useRef(null)
  const hours = heatmap?.hours ?? 48

  useEffect(() => {
    if (!playing) return undefined
    let previous = performance.now()
    let current = hour >= hours ? 0 : hour
    const tick = (now) => {
      current = Math.min(hours, current + ((now - previous) / 1000) * PLAYBACK_HOURS_PER_SECOND)
      previous = now
      onHourChange(current)
      if (current >= hours) {
        onPlayingChange(false)
        return
      }
      frameRef.current = requestAnimationFrame(tick)
    }
    frameRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frameRef.current)
    // Only (re)start when playback is toggled; `hour` is read once as the starting point.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, hours])

  const time = heatmap ? dayjs(heatmap.start).add(Math.floor(hour), 'hour') : null

  return (
    <Paper
      elevation={3}
      sx={{
        position: 'absolute',
        zIndex: 2,
        left: { xs: 8, sm: '50%' },
        right: { xs: 8, sm: 'auto' },
        bottom: { xs: 8, sm: 28 },
        transform: { sm: 'translateX(-50%)' },
        width: { sm: 460 },
        px: 2,
        py: 1.25,
      }}
    >
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
        <Typography variant="subtitle2" noWrap>
          Weather risk forecast
        </Typography>
        <FormControlLabel
          sx={{ mr: 0 }}
          control={
            <Switch size="small" checked={visible} onChange={(e) => onVisibleChange(e.target.checked)} />
          }
          label={<Typography variant="caption">Heatmap</Typography>}
        />
      </Stack>

      {error ? (
        <Alert
          severity="warning"
          sx={{ mt: 0.5, py: 0 }}
          action={
            <Button color="inherit" size="small" onClick={onRetry}>
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      ) : (
        <>
          <Stack direction="row" spacing={1.5} sx={{ alignItems: 'center' }}>
            <IconButton
              size="small"
              color="primary"
              disabled={!heatmap}
              onClick={() => onPlayingChange(!playing)}
              aria-label={playing ? 'Pause forecast' : 'Play forecast'}
            >
              {playing ? <PauseRoundedIcon /> : <PlayArrowRoundedIcon />}
            </IconButton>
            <Slider
              size="small"
              min={0}
              max={hours}
              step={1}
              marks={MARKS}
              value={hour}
              disabled={!heatmap}
              onChange={(_, value) => {
                onPlayingChange(false)
                onHourChange(value)
              }}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `+${Math.floor(value)}h`}
              aria-label="Hours after departure"
              sx={{ mx: 1 }}
            />
          </Stack>
          <Stack direction="row" sx={{ justifyContent: 'space-between', gap: 1, minHeight: 20 }}>
            {loading || !heatmap ? (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={12} />
                <Typography variant="caption" color="text.secondary">
                  Loading corridor forecast…
                </Typography>
              </Box>
            ) : (
              <>
                <Typography variant="caption" sx={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                  +{Math.floor(hour)}h · {time.format('ddd h:mm A')}
                </Typography>
                <Typography variant="caption" color="text.secondary" noWrap>
                  {truckStatus(truck, routeId)}
                </Typography>
              </>
            )}
          </Stack>
        </>
      )}
    </Paper>
  )
}
