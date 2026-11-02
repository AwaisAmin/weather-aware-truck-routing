import { Box, Card, CardActionArea, Chip, Stack, Typography } from '@mui/material'
import StarRoundedIcon from '@mui/icons-material/StarRounded'
import { riskColor } from '../constants/risk.js'
import { formatDateTime, formatDuration, formatMiles } from '../utils/format.js'
import RiskBar from './RiskBar.jsx'

function Stat({ label, value, emphasize }) {
  return (
    <Box sx={{ minWidth: 0 }}>
      <Typography variant="caption" color="text.secondary" noWrap component="div">
        {label}
      </Typography>
      <Typography
        variant="body2"
        sx={{
          fontWeight: 600,
          fontVariantNumeric: 'tabular-nums',
          color: emphasize ? 'error.main' : 'text.primary',
        }}
      >
        {value}
      </Typography>
    </Box>
  )
}

export default function RouteCard({ route, selected, onSelect }) {
  const { score } = route
  const miles = score.miles_by_level
  const severePlus = miles.severe + miles.no_travel
  return (
    <Card
      variant="outlined"
      sx={{
        borderColor: selected ? 'primary.main' : 'divider',
        borderWidth: selected ? 2 : 1,
        // Keep content aligned whether or not the thicker border is shown.
        m: selected ? 0 : '1px',
        transition: 'border-color 150ms',
      }}
    >
      <CardActionArea onClick={onSelect} aria-pressed={selected} sx={{ p: 1.5 }}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1 }}>
          <Box
            sx={{
              width: 26,
              height: 26,
              borderRadius: '50%',
              display: 'grid',
              placeItems: 'center',
              bgcolor: selected ? 'primary.main' : 'grey.500',
              color: 'common.white',
              fontWeight: 700,
              fontSize: 13,
              flexShrink: 0,
            }}
          >
            {route.id}
          </Box>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1 }}>
            {formatDuration(route.duration_s)}
            <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              {formatMiles(route.distance_miles)}
            </Typography>
          </Typography>
          {route.recommended && (
            <Chip size="small" color="primary" icon={<StarRoundedIcon />} label="Recommended" />
          )}
        </Stack>

        <RiskBar milesByLevel={miles} />

        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1, mt: 1.25 }}>
          <Stat label="Severe+" value={formatMiles(severePlus)} emphasize={severePlus > 0} />
          <Stat label="High" value={formatMiles(miles.high)} />
          <Stat label="Avg risk" value={score.average_risk.toFixed(2)} />
          <Box sx={{ minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary" noWrap component="div">
              Worst
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600, color: riskColor(score.max_level) }} noWrap>
              {score.max_label}
            </Typography>
          </Box>
        </Box>

        <Typography variant="caption" color="text.secondary" component="div" sx={{ mt: 1 }}>
          Arrives {formatDateTime(route.arrival)}
          {miles.no_travel > 0 && (
            <Box component="span" sx={{ color: riskColor(4), fontWeight: 600 }}>
              {' '}
              · {formatMiles(miles.no_travel)} No Travel
            </Box>
          )}
        </Typography>
      </CardActionArea>
    </Card>
  )
}
