import { memo } from 'react'
import { Box, List, ListItemButton, Typography } from '@mui/material'
import { riskColor } from '../constants/risk.js'
import { formatTime } from '../utils/format.js'

function weatherSummary({ wind_mph, rain_in_hr, snow_in_hr }) {
  const parts = [`${Math.round(wind_mph)} mph`]
  if (rain_in_hr > 0) parts.push(`rain ${rain_in_hr}"`)
  if (snow_in_hr > 0) parts.push(`snow ${snow_in_hr}"`)
  return parts.join(' · ')
}

function CheckpointList({ route, focusedIndex, onFocus }) {
  return (
    <List dense disablePadding aria-label={`Route ${route.id} checkpoints`}>
      {route.checkpoints.map((checkpoint) => (
        <ListItemButton
          key={checkpoint.index}
          selected={checkpoint.index === focusedIndex}
          onClick={() => onFocus(checkpoint.index)}
          sx={{ gap: 1.5, borderRadius: 1, py: 0.5 }}
        >
          <Box
            sx={{
              width: 10,
              height: 10,
              borderRadius: '50%',
              bgcolor: riskColor(checkpoint.risk.level),
              flexShrink: 0,
            }}
          />
          <Typography variant="body2" sx={{ width: 56, fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
            {Math.round(checkpoint.mile)} mi
          </Typography>
          <Typography variant="body2" sx={{ width: 92, fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
            {formatTime(checkpoint.eta)}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap sx={{ flex: 1, minWidth: 0 }}>
            {weatherSummary(checkpoint.weather)}
          </Typography>
          <Typography
            variant="caption"
            sx={{ fontWeight: 600, color: riskColor(checkpoint.risk.level), flexShrink: 0 }}
          >
            {checkpoint.risk.label}
          </Typography>
        </ListItemButton>
      ))}
    </List>
  )
}

export default memo(CheckpointList)
