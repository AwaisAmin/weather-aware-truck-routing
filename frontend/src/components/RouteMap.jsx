import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Map, { Layer, Marker, NavigationControl, Popup, Source } from 'react-map-gl/maplibre'
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { Box } from '@mui/material'
import 'maplibre-gl/dist/maplibre-gl.css'
import { RISK_COLOR_EXPRESSION } from '../constants/risk.js'
import CheckpointPopup from './CheckpointPopup.jsx'
import ForecastOverlay from './ForecastOverlay.jsx'
import MapLegend from './MapLegend.jsx'

// MapLibre locates its worker relative to its own module, which breaks once Vite bundles it.
setWorkerUrl(workerUrl)

const MAP_STYLE = 'https://tiles.openfreemap.org/styles/positron'
const INITIAL_VIEW = { longitude: -98.5, latitude: 39.5, zoom: 3.6 }
const SELECTED_COLOR = '#1f5fbf'
const OTHER_COLOR = '#8a99a8'
const INTERACTIVE_LAYERS = ['checkpoints', 'routes-hit']

function routesToGeoJSON(routes) {
  return {
    type: 'FeatureCollection',
    features: routes.map((route) => ({
      type: 'Feature',
      properties: { routeId: route.id },
      geometry: { type: 'LineString', coordinates: route.geometry },
    })),
  }
}

function checkpointsToGeoJSON(routes) {
  return {
    type: 'FeatureCollection',
    features: routes.flatMap((route) =>
      route.checkpoints.map((checkpoint) => ({
        type: 'Feature',
        properties: { routeId: route.id, index: checkpoint.index, level: checkpoint.risk.level },
        geometry: { type: 'Point', coordinates: [checkpoint.lon, checkpoint.lat] },
      })),
    ),
  }
}

function boundsOf(routes) {
  let [minLon, minLat, maxLon, maxLat] = [180, 90, -180, -90]
  for (const route of routes) {
    for (const [lon, lat] of route.geometry) {
      minLon = Math.min(minLon, lon)
      minLat = Math.min(minLat, lat)
      maxLon = Math.max(maxLon, lon)
      maxLat = Math.max(maxLat, lat)
    }
  }
  return [
    [minLon, minLat],
    [maxLon, maxLat],
  ]
}

/**
 * focus: { routeId, index, fromList } | null — the checkpoint whose popup is open.
 * When it was chosen from the sidebar list, the map pans to it.
 */
export default function RouteMap({
  plan,
  selectedRouteId,
  onSelectRoute,
  focus,
  onFocus,
  heatmapState,
  onRetryHeatmap,
}) {
  const mapRef = useRef(null)
  const [cursor, setCursor] = useState('')
  const routes = useMemo(() => plan?.routes ?? [], [plan])

  // Rebuilt only when a new plan arrives; selection is handled in paint expressions.
  const routesData = useMemo(() => routesToGeoJSON(routes), [routes])
  const checkpointsData = useMemo(() => checkpointsToGeoJSON(routes), [routes])
  const labelCoordinates = useMemo(() => labelPositions(routes), [routes])
  const isSelected = useMemo(() => ['==', ['get', 'routeId'], selectedRouteId ?? ''], [selectedRouteId])

  const fitToPlan = useCallback(() => {
    if (!mapRef.current || routes.length === 0) return
    mapRef.current.fitBounds(boundsOf(routes), { padding: 60, duration: 800 })
  }, [routes])

  useEffect(fitToPlan, [fitToPlan])

  const focusedRoute = focus ? routes.find((r) => r.id === focus.routeId) : null
  const focusedCheckpoint = focusedRoute?.checkpoints[focus.index] ?? null

  useEffect(() => {
    if (focus?.fromList && focusedCheckpoint && mapRef.current) {
      mapRef.current.easeTo({ center: [focusedCheckpoint.lon, focusedCheckpoint.lat], duration: 600 })
    }
  }, [focus, focusedCheckpoint])

  const handleClick = useCallback(
    (event) => {
      const feature = event.features?.[0]
      if (!feature) {
        onFocus(null)
        return
      }
      const { routeId, index } = feature.properties
      onSelectRoute(routeId)
      onFocus(feature.layer.id === 'checkpoints' ? { routeId, index, fromList: false } : null)
    },
    [onSelectRoute, onFocus],
  )

  const routeLinePaint = useMemo(
    () => ({
      'line-color': ['case', isSelected, SELECTED_COLOR, OTHER_COLOR],
      'line-width': ['case', isSelected, 6, 4],
      'line-opacity': ['case', isSelected, 1, 0.75],
    }),
    [isSelected],
  )

  const checkpointPaint = useMemo(
    () => ({
      'circle-color': RISK_COLOR_EXPRESSION,
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        4,
        ['case', isSelected, 4, 2.5],
        9,
        ['case', isSelected, 8, 5],
      ],
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': ['case', isSelected, 1.5, 0.75],
      'circle-opacity': ['case', isSelected, 1, 0.6],
      'circle-stroke-opacity': ['case', isSelected, 1, 0.6],
    }),
    [isSelected],
  )

  // Draw the selected route and its checkpoints above the others.
  const sortKey = useMemo(() => ['case', isSelected, 1, 0], [isSelected])

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
      <Map
        ref={mapRef}
        initialViewState={INITIAL_VIEW}
        mapStyle={MAP_STYLE}
        interactiveLayerIds={routes.length ? INTERACTIVE_LAYERS : []}
        cursor={cursor}
        onClick={handleClick}
        onMouseEnter={() => setCursor('pointer')}
        onMouseLeave={() => setCursor('')}
        onLoad={fitToPlan}
        style={{ width: '100%', height: '100%' }}
      >
        <NavigationControl position="top-right" showCompass={false} />

        <Source id="routes" type="geojson" data={routesData}>
          <Layer
            id="routes-casing"
            type="line"
            layout={{ 'line-join': 'round', 'line-cap': 'round', 'line-sort-key': sortKey }}
            paint={{ 'line-color': '#ffffff', 'line-width': ['case', isSelected, 10, 7] }}
          />
          <Layer
            id="routes-line"
            type="line"
            layout={{ 'line-join': 'round', 'line-cap': 'round', 'line-sort-key': sortKey }}
            paint={routeLinePaint}
          />
          {/* Wide invisible line so routes are easy to click or tap. */}
          <Layer
            id="routes-hit"
            type="line"
            paint={{ 'line-color': '#000000', 'line-width': 16, 'line-opacity': 0 }}
          />
        </Source>

        <Source id="checkpoints" type="geojson" data={checkpointsData}>
          <Layer
            id="checkpoints"
            type="circle"
            layout={{ 'circle-sort-key': sortKey }}
            paint={checkpointPaint}
          />
        </Source>

        {routes.map((route, index) => (
          <RouteLabel
            key={route.id}
            route={route}
            position={labelCoordinates[index]}
            selected={route.id === selectedRouteId}
            onSelect={() => onSelectRoute(route.id)}
          />
        ))}

        {plan && (
          <>
            <EndpointMarker lon={plan.origin.lon} lat={plan.origin.lat} color="#2e7d32" />
            <EndpointMarker lon={plan.destination.lon} lat={plan.destination.lat} color="#c62828" />
          </>
        )}

        {plan && (
          <ForecastOverlay
            heatmap={heatmapState.data}
            loading={heatmapState.loading}
            error={heatmapState.error}
            onRetry={onRetryHeatmap}
            selectedRoute={routes.find((r) => r.id === selectedRouteId)}
          />
        )}

        {focusedCheckpoint && (
          <Popup
            longitude={focusedCheckpoint.lon}
            latitude={focusedCheckpoint.lat}
            offset={12}
            maxWidth="280px"
            closeOnClick={false}
            onClose={() => onFocus(null)}
          >
            <CheckpointPopup route={focusedRoute} checkpoint={focusedCheckpoint} />
          </Popup>
        )}
      </Map>
      {plan && <MapLegend />}
    </Box>
  )
}

const LABEL_SAMPLES = 60

/** For each route, the vertex farthest from every other route, so labels sit where routes diverge. */
function labelPositions(routes) {
  const sample = (route) => {
    const step = Math.max(1, Math.floor(route.geometry.length / LABEL_SAMPLES))
    return route.geometry.filter((_, i) => i % step === 0)
  }
  const samples = routes.map(sample)
  return routes.map((route, routeIndex) => {
    const others = samples.filter((_, i) => i !== routeIndex).flat()
    let best = route.geometry[Math.floor(route.geometry.length / 2)]
    let bestDistance = -1
    // Skip the ends, which all routes share.
    for (const point of samples[routeIndex].slice(2, -2)) {
      let nearest = Infinity
      for (const other of others) {
        nearest = Math.min(nearest, (point[0] - other[0]) ** 2 + (point[1] - other[1]) ** 2)
      }
      if (nearest > bestDistance) {
        bestDistance = nearest
        best = point
      }
    }
    return best
  })
}

function RouteLabel({ route, position, selected, onSelect }) {
  const [lon, lat] = position
  return (
    <Marker longitude={lon} latitude={lat} anchor="center" style={{ zIndex: selected ? 2 : 1 }}>
      <Box
        component="button"
        type="button"
        onClick={(event) => {
          event.stopPropagation()
          onSelect()
        }}
        aria-label={`Select route ${route.id}`}
        sx={{
          border: 2,
          borderColor: 'common.white',
          borderRadius: '50%',
          width: 28,
          height: 28,
          p: 0,
          cursor: 'pointer',
          font: 'inherit',
          fontWeight: 700,
          fontSize: 13,
          color: 'common.white',
          bgcolor: selected ? SELECTED_COLOR : OTHER_COLOR,
          boxShadow: 2,
        }}
      >
        {route.id}
      </Box>
    </Marker>
  )
}

function EndpointMarker({ lon, lat, color }) {
  return (
    <Marker longitude={lon} latitude={lat} anchor="center">
      <Box
        sx={{
          width: 16,
          height: 16,
          borderRadius: '50%',
          bgcolor: color,
          border: 3,
          borderColor: 'common.white',
          boxShadow: 2,
        }}
      />
    </Marker>
  )
}
