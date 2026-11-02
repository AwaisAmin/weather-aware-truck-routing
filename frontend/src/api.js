const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(errorMessage(body) ?? `Request failed (${response.status})`)
  }
  return body
}

// DRF errors are either {detail: "..."} or {field: ["..."], ...}.
function errorMessage(body) {
  if (!body || typeof body !== 'object') return null
  if (typeof body.detail === 'string') return body.detail
  const first = Object.values(body).flat()[0]
  return typeof first === 'string' ? first : null
}

export function apiGet(path, { signal } = {}) {
  return request(path, { signal })
}

export function searchPlaces(query, { signal } = {}) {
  return request(`/api/geocode/?q=${encodeURIComponent(query)}`, { signal }).then((data) => data.results)
}

export function planTrip(payload, { signal } = {}) {
  return request('/api/plan/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
}

export function fetchHeatmap(payload, { signal } = {}) {
  return request('/api/heatmap/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
}
