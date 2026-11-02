import { Box, Chip, Stack, Typography } from '@mui/material'
import { riskColor } from '../constants/risk.js'
import { formatDateTime } from '../utils/format.js'

const DRIVER_LABELS = { wind: 'Wind', rain: 'Rain', snow: 'Snow', 'wind+load': 'Wind × load weight' }

function Row({ label, value }) {
  return (
    <Stack direction="row" sx={{ justifyContent: 'space-between', gap: 2 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </Typography>
    </Stack>
  )
}

export default function CheckpointPopup({ route, checkpoint }) {
  const { weather, risk } = checkpoint
  return (
    <Box sx={{ minWidth: 220, pr: 1 }}>
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="subtitle2">
          Route {route.id} · mile {Math.round(checkpoint.mile)}
        </Typography>
        <Chip
          size="small"
          label={risk.label}
          sx={{ bgcolor: riskColor(risk.level), color: 'common.white', fontWeight: 600 }}
        />
      </Stack>
      <Row label="ETA" value={formatDateTime(checkpoint.eta)} />
      <Row label="Wind" value={`${weather.wind_mph} mph (gusts ${weather.gust_mph})`} />
      <Row label="Rain" value={`${weather.rain_in_hr} in/hr`} />
      <Row label="Snow" value={`${weather.snow_in_hr} in/hr`} />
      <Row label="Temperature" value={`${weather.temp_f} °F`} />
      {risk.drivers.length > 0 && (
        <Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 1 }}>
          Driven by: {risk.drivers.map((d) => DRIVER_LABELS[d] ?? d).join(', ')}
        </Typography>
      )}
    </Box>
  )
}
