// Index matches the backend RiskLevel value (Low=0 ... No Travel=4).
export const RISK_LEVELS = [
  { key: 'low', label: 'Low', color: '#2e7d32' },
  { key: 'moderate', label: 'Moderate', color: '#f2b600' },
  { key: 'high', label: 'High', color: '#ef6c00' },
  { key: 'severe', label: 'Severe', color: '#d32f2f' },
  { key: 'no_travel', label: 'No Travel', color: '#6a1b9a' },
]

export const riskColor = (level) => RISK_LEVELS[level]?.color ?? '#9e9e9e'

// MapLibre expression mapping a feature's numeric `level` property to its color.
export const RISK_COLOR_EXPRESSION = [
  'match',
  ['get', 'level'],
  ...RISK_LEVELS.flatMap((risk, level) => [level, risk.color]),
  '#9e9e9e',
]
