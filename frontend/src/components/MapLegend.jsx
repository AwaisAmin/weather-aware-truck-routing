import { Box, Paper, Typography } from '@mui/material'
import { RISK_LEVELS } from '../constants/risk.js'

export default function MapLegend() {
  return (
    <Paper
      elevation={2}
      sx={{
        position: 'absolute',
        left: { xs: 8, md: 12 },
        top: { xs: 8, md: 12 },
        right: { xs: 8, md: 'auto' },
        zIndex: 1,
        px: { xs: 1, md: 1.5 },
        py: { xs: 0.5, md: 1 },
        // A single row on small screens so it covers less of the map.
        display: 'flex',
        flexDirection: { xs: 'row', md: 'column' },
        flexWrap: 'wrap',
        justifyContent: { xs: 'space-between', md: 'flex-start' },
        gap: { xs: 1, md: 0.5 },
      }}
    >
      <Typography variant="caption" sx={{ fontWeight: 600, display: { xs: 'none', md: 'block' } }}>
        Risk level
      </Typography>
      {RISK_LEVELS.map((risk) => (
        <Box key={risk.key} sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
          <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: risk.color }} />
          <Typography variant="caption" noWrap>
            {risk.label}
          </Typography>
        </Box>
      ))}
    </Paper>
  )
}
