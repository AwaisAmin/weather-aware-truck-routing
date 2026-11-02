import { Component } from 'react'
import { Alert, Box } from '@mui/material'

/** Keeps the form and results usable if the map cannot render (e.g. WebGL is unavailable). */
export default class MapErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <Box sx={{ height: '100%', display: 'grid', placeItems: 'center', p: 2 }}>
          <Alert severity="warning">
            The map could not be displayed. Your browser may not support WebGL. Route results are still
            available in the panel.
          </Alert>
        </Box>
      )
    }
    return this.props.children
  }
}
