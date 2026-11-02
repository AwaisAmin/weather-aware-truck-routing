import { useEffect, useState } from 'react'
import { Autocomplete, CircularProgress, InputAdornment, TextField } from '@mui/material'
import PlaceOutlinedIcon from '@mui/icons-material/PlaceOutlined'
import { searchPlaces } from '../api.js'
import useDebouncedValue from '../hooks/useDebouncedValue.js'

const MIN_QUERY_LENGTH = 2
const DEBOUNCE_MS = 300

export default function PlaceAutocomplete({ label, value, onChange, error, helperText, disabled }) {
  const [inputValue, setInputValue] = useState(value?.label ?? '')
  const [previousValue, setPreviousValue] = useState(value)
  // Show the new label when the value is changed from outside (e.g. origin/destination swap).
  if (value !== previousValue) {
    setPreviousValue(value)
    setInputValue(value?.label ?? '')
  }
  const [options, setOptions] = useState([])
  // The query whose results are currently in `options`.
  const [resolvedQuery, setResolvedQuery] = useState('')
  const query = useDebouncedValue(inputValue.trim(), DEBOUNCE_MS)
  // Typing the selected label back in should not trigger another search.
  const shouldSearch = query.length >= MIN_QUERY_LENGTH && query !== value?.label
  const loading = shouldSearch && resolvedQuery !== query

  useEffect(() => {
    if (!shouldSearch || resolvedQuery === query) return undefined
    const controller = new AbortController()
    searchPlaces(query, { signal: controller.signal })
      .then((results) => {
        setOptions(results)
        setResolvedQuery(query)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setOptions([])
        setResolvedQuery(query)
      })
    return () => controller.abort()
  }, [query, shouldSearch, resolvedQuery])

  return (
    <Autocomplete
      value={value}
      inputValue={inputValue}
      options={value && !options.includes(value) ? [value, ...options] : options}
      loading={loading}
      disabled={disabled}
      // Results are already filtered by the geocoder.
      filterOptions={(x) => x}
      getOptionLabel={(option) => option.label}
      getOptionKey={(option) => `${option.label}-${option.lat}-${option.lon}`}
      isOptionEqualToValue={(a, b) => a.lat === b.lat && a.lon === b.lon}
      noOptionsText={inputValue.trim().length < MIN_QUERY_LENGTH ? 'Type a city or address' : 'No places found'}
      onChange={(_, place) => onChange(place)}
      onInputChange={(_, text) => setInputValue(text)}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          error={error}
          helperText={helperText}
          slotProps={{
            ...params.slotProps,
            input: {
              ...params.slotProps.input,
              startAdornment: (
                <InputAdornment position="start">
                  <PlaceOutlinedIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
              endAdornment: (
                <>
                  {loading ? <CircularProgress color="inherit" size={18} /> : null}
                  {params.slotProps.input.endAdornment}
                </>
              ),
            },
          }}
        />
      )}
    />
  )
}
