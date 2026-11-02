import { useState } from 'react'
import dayjs from 'dayjs'
import {
  Box,
  Button,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from '@mui/material'
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker'
import SwapVertIcon from '@mui/icons-material/SwapVert'
import RouteIcon from '@mui/icons-material/Route'
import PlaceAutocomplete from './PlaceAutocomplete.jsx'

// Keep in sync with backend/routing/serializers.py.
const MAX_DAYS_AHEAD = 5
const MAX_LOAD_LB = 100_000
const SAMPLE_INTERVALS = [10, 25, 50]

function nextHour() {
  return dayjs().add(1, 'hour').startOf('hour')
}

function validate({ origin, destination, departure, load }) {
  const errors = {}
  if (!origin) errors.origin = 'Choose a starting point'
  if (!destination) errors.destination = 'Choose a destination'
  if (origin && destination && origin.lat === destination.lat && origin.lon === destination.lon) {
    errors.destination = 'Destination must differ from origin'
  }
  if (!departure?.isValid()) errors.departure = 'Enter a valid date and time'
  else if (departure.isAfter(dayjs().add(MAX_DAYS_AHEAD, 'day'))) {
    errors.departure = `Must be within ${MAX_DAYS_AHEAD} days`
  }
  const weight = Number(load)
  if (load === '' || !Number.isFinite(weight) || weight < 0 || weight > MAX_LOAD_LB) {
    errors.load = `Enter 0 – ${MAX_LOAD_LB.toLocaleString()} lb`
  }
  return errors
}

export default function TripForm({ loading, onSubmit }) {
  const [origin, setOrigin] = useState(null)
  const [destination, setDestination] = useState(null)
  const [departure, setDeparture] = useState(nextHour)
  const [load, setLoad] = useState('35000')
  const [intervalMiles, setIntervalMiles] = useState(25)
  const [errors, setErrors] = useState({})

  const handleSubmit = (event) => {
    event.preventDefault()
    const nextErrors = validate({ origin, destination, departure, load })
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return
    onSubmit({
      origin,
      destination,
      departure: departure.toISOString(),
      load_lb: Number(load),
      interval_miles: intervalMiles,
    })
  }

  const swap = () => {
    setOrigin(destination)
    setDestination(origin)
  }

  return (
    <Box component="form" noValidate onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Stack spacing={2} sx={{ flex: 1, minWidth: 0 }}>
            <PlaceAutocomplete
              // Remount on swap so each field shows its new place's label.
              key={`origin-${origin?.label ?? ''}`}
              label="Origin"
              value={origin}
              onChange={setOrigin}
              error={Boolean(errors.origin)}
              helperText={errors.origin}
              disabled={loading}
            />
            <PlaceAutocomplete
              key={`destination-${destination?.label ?? ''}`}
              label="Destination"
              value={destination}
              onChange={setDestination}
              error={Boolean(errors.destination)}
              helperText={errors.destination}
              disabled={loading}
            />
          </Stack>
          <Tooltip title="Swap origin and destination">
            <span>
              <IconButton onClick={swap} disabled={loading || (!origin && !destination)} aria-label="Swap">
                <SwapVertIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>

        <DateTimePicker
          label="Departure"
          value={departure}
          onChange={setDeparture}
          disablePast
          maxDateTime={dayjs().add(MAX_DAYS_AHEAD, 'day')}
          disabled={loading}
          slotProps={{
            textField: { error: Boolean(errors.departure), helperText: errors.departure, fullWidth: true },
          }}
        />

        <TextField
          label="Load weight"
          type="number"
          value={load}
          onChange={(event) => setLoad(event.target.value)}
          error={Boolean(errors.load)}
          helperText={errors.load ?? 'Cargo only; a 35,000 lb tractor-trailer is assumed'}
          disabled={loading}
          slotProps={{
            input: { endAdornment: <InputAdornment position="end">lb</InputAdornment> },
            htmlInput: { min: 0, max: MAX_LOAD_LB, step: 1000, inputMode: 'numeric' },
          }}
        />

        <Box>
          <Typography variant="caption" color="text.secondary" component="div" sx={{ mb: 0.5 }}>
            Weather checkpoint every
          </Typography>
          <ToggleButtonGroup
            exclusive
            fullWidth
            size="small"
            color="primary"
            value={intervalMiles}
            disabled={loading}
            onChange={(_, value) => value && setIntervalMiles(value)}
          >
            {SAMPLE_INTERVALS.map((miles) => (
              <ToggleButton key={miles} value={miles}>
                {miles} mi
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>

        <Button
          type="submit"
          variant="contained"
          size="large"
          loading={loading}
          loadingPosition="start"
          startIcon={<RouteIcon />}
        >
          {loading ? 'Planning routes…' : 'Find safest route'}
        </Button>
      </Stack>
    </Box>
  )
}
