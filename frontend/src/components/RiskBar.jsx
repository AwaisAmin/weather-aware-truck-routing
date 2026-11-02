import { Box, Tooltip } from '@mui/material'
import { RISK_LEVELS } from '../constants/risk.js'

/** Horizontal bar splitting a route's miles by risk level. */
export default function RiskBar({ milesByLevel, height = 8 }) {
  const total = RISK_LEVELS.reduce((sum, risk) => sum + (milesByLevel[risk.key] ?? 0), 0)
  return (
    <Box
      role="img"
      aria-label="Miles by risk level"
      sx={{ display: 'flex', height, borderRadius: height / 2, overflow: 'hidden', bgcolor: 'action.hover' }}
    >
      {total > 0 &&
        RISK_LEVELS.map((risk) => {
          const miles = milesByLevel[risk.key] ?? 0
          if (miles <= 0) return null
          return (
            <Tooltip key={risk.key} title={`${risk.label}: ${Math.round(miles)} mi`} arrow>
              <Box sx={{ width: `${(miles / total) * 100}%`, bgcolor: risk.color }} />
            </Tooltip>
          )
        })}
    </Box>
  )
}
