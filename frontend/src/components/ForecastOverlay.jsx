import { useMemo, useState } from 'react'
import dayjs from 'dayjs'
import { truckPositionAt } from '../utils/route.js'
import HeatmapControl from './HeatmapControl.jsx'
import WeatherHeatmap from './WeatherHeatmap.jsx'

/**
 * Heatmap layer, forecast slider and truck marker. Kept apart from the route layers so that
 * moving the slider re-renders only this subtree.
 */
export default function ForecastOverlay({ heatmap, loading, error, onRetry, selectedRoute }) {
  const [hour, setHour] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [visible, setVisible] = useState(true)
  const [previousHeatmap, setPreviousHeatmap] = useState(heatmap)
  // Start each new forecast from departure.
  if (heatmap !== previousHeatmap) {
    setPreviousHeatmap(heatmap)
    setHour(0)
    setPlaying(false)
  }

  const truck = useMemo(() => {
    if (!heatmap || !selectedRoute) return null
    const timeMs = dayjs(heatmap.start).valueOf() + hour * 3_600_000
    return truckPositionAt(selectedRoute, timeMs)
  }, [heatmap, selectedRoute, hour])

  return (
    <>
      {heatmap && <WeatherHeatmap heatmap={heatmap} hour={hour} visible={visible} truck={truck} />}
      <HeatmapControl
        heatmap={heatmap}
        loading={loading}
        error={error}
        onRetry={onRetry}
        hour={hour}
        onHourChange={setHour}
        playing={playing}
        onPlayingChange={setPlaying}
        visible={visible}
        onVisibleChange={setVisible}
        truck={truck}
        routeId={selectedRoute?.id}
      />
    </>
  )
}
