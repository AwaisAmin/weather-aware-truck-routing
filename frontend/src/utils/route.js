/**
 * Where the truck is on a route at a given time, interpolated between checkpoints.
 * Returns { lon, lat, mile, status } where status is 'waiting', 'driving' or 'arrived'.
 */
export function truckPositionAt(route, timeMs) {
  const checkpoints = route.checkpoints
  const times = checkpoints.map((c) => Date.parse(c.eta))
  const first = checkpoints[0]
  const last = checkpoints[checkpoints.length - 1]
  if (timeMs < times[0]) return { lon: first.lon, lat: first.lat, mile: 0, status: 'waiting' }
  if (timeMs >= times[times.length - 1])
    return { lon: last.lon, lat: last.lat, mile: last.mile, status: 'arrived' }

  let i = 1
  while (times[i] < timeMs) i += 1
  const a = checkpoints[i - 1]
  const b = checkpoints[i]
  const t = (timeMs - times[i - 1]) / (times[i] - times[i - 1] || 1)
  return {
    lon: a.lon + (b.lon - a.lon) * t,
    lat: a.lat + (b.lat - a.lat) * t,
    mile: a.mile + (b.mile - a.mile) * t,
    status: 'driving',
  }
}

/** Every nth point so a geometry has at most maxPoints (always keeping the last point). */
export function downsample(coordinates, maxPoints) {
  if (coordinates.length <= maxPoints) return coordinates
  const step = Math.ceil(coordinates.length / (maxPoints - 1))
  const result = coordinates.filter((_, i) => i % step === 0)
  result.push(coordinates[coordinates.length - 1])
  return result
}
