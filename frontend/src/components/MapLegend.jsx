import { Box, Paper, Typography } from '@mui/material'
import { RISK_LEVELS } from '../constants/risk.js'

export default function MapLegend() {
  return (
    <Paper
      elevation={2}
      sx={{ position: 'absolute', left: 12, top: 12, px: 1.5, py: 1, display: 'grid', gap: 0.5, zIndex: 1 }}
    >
      <Typography variant="caption" sx={{ fontWeight: 600 }}>
        Risk level
      </Typography>
      {RISK_LEVELS.map((risk) => (
        <Box key={risk.key} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: risk.color }} />
          <Typography variant="caption">{risk.label}</Typography>
        </Box>
      ))}
    </Paper>
  )
}
