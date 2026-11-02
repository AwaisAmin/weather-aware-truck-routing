import { useCallback, useMemo, useState } from 'react'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { ColorModeContext } from './colorModeContext.js'
import { createAppTheme } from './theme.js'

const STORAGE_KEY = 'color-mode'

function readStoredMode() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'light' || stored === 'dark' ? stored : null
  } catch {
    return null
  }
}

/** Light theme by default; the user's choice of dark mode is remembered. */
export default function ColorModeProvider({ children }) {
  const [mode, setMode] = useState(() => readStoredMode() ?? 'light')

  const toggleMode = useCallback(() => {
    const next = mode === 'dark' ? 'light' : 'dark'
    setMode(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Storage can be unavailable (private mode); the choice then lasts for this visit.
    }
  }, [mode])

  const theme = useMemo(() => createAppTheme(mode), [mode])
  const value = useMemo(() => ({ mode, toggleMode }), [mode, toggleMode])

  return (
    <ColorModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline enableColorScheme />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  )
}
