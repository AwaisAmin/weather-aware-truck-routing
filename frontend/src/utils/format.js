import dayjs from 'dayjs'

export function formatDuration(seconds) {
  const totalMinutes = Math.round(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return hours > 0 ? `${hours} h ${String(minutes).padStart(2, '0')} min` : `${minutes} min`
}

export function formatMiles(miles) {
  return `${Math.round(miles).toLocaleString()} mi`
}

// Times are shown in the viewer's local time zone.
export function formatDateTime(iso) {
  return dayjs(iso).format('ddd MMM D, h:mm A')
}

export function formatTime(iso) {
  return dayjs(iso).format('ddd h:mm A')
}
