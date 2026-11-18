# Changelog

## 0.1.1

- Use `UnitOfDensity` / `UnitOfRatio` for air quality units instead of the deprecated `CONCENTRATION_*` constants (removed in Home Assistant 2027.8). Older Home Assistant versions keep working.

## 0.1.0

First version.

- Config flow: name, location, weather model (Best match by default), air quality on/off, forecast days, 15-minute data.
- Options flow to change all of these later; changing the model checks it covers the location.
- Weather entity with daily and hourly forecast.
- Sensors for current values, today, next hour (15-minute data) and air quality/pollen. Only for values the chosen model provides.
- English and Danish translations.
