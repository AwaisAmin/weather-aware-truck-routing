import { useMemo } from 'react'
import { Layer, Marker, Source } from 'react-map-gl/maplibre'
import { Box } from '@mui/material'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import { RISK_LEVELS } from '../constants/risk.js'

// MapLibre heatmap kernel: density at a lone point's centre is weight * intensity * GAUSS_COEF,
// with a Gaussian of sigma = radius / 3. For a regular grid of spacing s (px) the kernels sum
// to about weight * intensity * 0.2785 * radius^2 / s^2, so we pick the radius as a multiple of
// the spacing and set intensity to cancel it out: a uniform field of score x then has density x / 4.
const RADIUS_TO_SPACING = 1.4
const KERNEL_SUM_PER_UNIT = 0.2785
const TILE_SIZE = 512

function heatmapToGeoJSON(heatmap) {
  return {
    type: 'FeatureCollection',
    features: heatmap.cells.map((coordinates, i) => {
      const properties = {}
      heatmap.scores[i].forEach((score, hour) => {
        properties[`s${hour}`] = score / 10
      })
      return { type: 'Feature', properties, geometry: { type: 'Point', coordinates } }
    }),
  }
}

function heatmapPaint(heatmap, hour) {
  const latitudes = heatmap.cells.map(([, lat]) => lat)
  const midLat = (Math.min(...latitudes) + Math.max(...latitudes)) / 2
  const cosLat = Math.cos((midLat * Math.PI) / 180)
  // Grid spacing in pixels at zoom 0: east-west, and north-south (stretched by Mercator).
  const spacingX = (heatmap.spacing_deg * TILE_SIZE) / 360
  const spacingY = spacingX / cosLat
  const radiusAtZoom0 = RADIUS_TO_SPACING * spacingY
  const intensity = (spacingX * spacingY) / (KERNEL_SUM_PER_UNIT * radiusAtZoom0 ** 2)

  // Blend neighbouring hours so playback animates smoothly between forecast steps.
  const lower = Math.floor(hour)
  const upper = Math.min(lower + 1, heatmap.hours)
  const fraction = hour - lower
  const score =
    fraction === 0
      ? ['get', `s${lower}`]
      : ['+', ['*', ['get', `s${lower}`], 1 - fraction], ['*', ['get', `s${upper}`], fraction]]

  return {
    'heatmap-weight': ['/', score, 4],
    'heatmap-intensity': intensity,
    'heatmap-radius': [
      'interpolate',
      ['exponential', 2],
      ['zoom'],
      0,
      radiusAtZoom0,
      12,
      radiusAtZoom0 * 4096,
    ],
    // Density equals score / 4, so these stops line up with the risk levels.
    'heatmap-color': [
      'interpolate',
      ['linear'],
      ['heatmap-density'],
      0,
      'rgba(0,0,0,0)',
      0.2,
      'rgba(0,0,0,0)',
      0.25,
      RISK_LEVELS[1].color,
      0.5,
      RISK_LEVELS[2].color,
      0.75,
      RISK_LEVELS[3].color,
      1,
      RISK_LEVELS[4].color,
    ],
    'heatmap-opacity': 0.55,
  }
}

/** Heatmap layer (drawn under the routes) plus a truck marker for the selected route. */
export default function WeatherHeatmap({ heatmap, hour, visible, truck }) {
  const data = useMemo(() => heatmapToGeoJSON(heatmap), [heatmap])
  const paint = useMemo(() => heatmapPaint(heatmap, hour), [heatmap, hour])

  return (
    <>
      <Source id="weather-heatmap" type="geojson" data={data}>
        <Layer
          id="weather-heatmap"
          type="heatmap"
          beforeId="routes-casing"
          layout={{ visibility: visible ? 'visible' : 'none' }}
          paint={paint}
        />
      </Source>
      {truck && (
        <Marker longitude={truck.lon} latitude={truck.lat} anchor="center" style={{ zIndex: 3 }}>
          <Box
            sx={{
              width: 30,
              height: 30,
              borderRadius: '50%',
              display: 'grid',
              placeItems: 'center',
              bgcolor: 'common.black',
              color: 'common.white',
              border: 2,
              borderColor: 'common.white',
              boxShadow: 3,
              pointerEvents: 'none',
            }}
          >
            <LocalShippingIcon sx={{ fontSize: 17 }} />
          </Box>
        </Marker>
      )}
    </>
  )
}
