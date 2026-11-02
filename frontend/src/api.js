const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function apiGet(path, { signal } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, { signal })
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`)
  }
  return response.json()
}
