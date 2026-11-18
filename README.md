# Open-Meteo Weather for Home Assistant

A Home Assistant integration for the free [Open-Meteo](https://open-meteo.com) weather API. You can pick which weather model to use, and it adds air quality and pollen.

- **Model selection:** **Best match** by default, or any of Open-Meteo's ~50 models. Examples are DMI Harmonie, MET Norway Nordic, ECMWF IFS, DWD ICON, KNMI, Météo-France and UK Met Office. Change it any time under **Configure**.
- **Weather entity** with current conditions, plus a daily and an hourly forecast of up to 16 days.
- **100+ sensors.** Current values are refreshed every 15 minutes, along with today's values and the next hour from 15-minute data. The less common ones (soil, radiation details, CAPE, winds at 80 m) are turned off by default.
- **Sensors follow the model.** A sensor is only created if the chosen model has the value. For example, the DMI models have no UV index and ECMWF has no visibility. Switching model removes sensors the new model can't fill.
- **Air quality and pollen** (optional, on by default) from CAMS, every hour:
  - European and US AQI
  - PM2.5, PM10, NO₂, O₃, SO₂, CO, CO₂, dust
  - Alder, birch, grass, mugwort, olive and ragweed pollen (Europe)
- **Several entries per location** with different models, to compare them side by side.
- English and Danish.

## Installation

### HACS

1. In HACS, add `https://github.com/briis/ha-openmeteo` as a custom repository (type *Integration*).
2. Install **Open-Meteo Weather** and restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration → Open-Meteo Weather**.

### Manual

Copy `custom_components/openmeteo_weather` to your `config/custom_components/` folder and restart.

## Configuration

| Option | Default | |
|---|---|---|
| Name | Open-Meteo | Device name, used in entity ids |
| Location | Home | Point on the map |
| Weather model | Best match | Regional models only work inside their area. Setup checks this. |
| Air quality and pollen | On | Separate request every hour. Can be turned off later. |
| Forecast days | 7 | 1-16 |
| 15-minute data | On | Precipitation and gusts in the next hour |

Everything except name and location can be changed later under **Configure**.

## Entities

**Weather:** `weather.<name>` provides the condition, temperature, feels-like, dew point, humidity, pressure, wind, gusts, cloud cover, UV index and visibility. It has daily and hourly forecasts (`weather.get_forecasts`).

**Sensors enabled by default:**
- Current: temperature, feels like, dew point, humidity, precipitation, chance of precipitation, cloud cover, pressure, wind speed, direction and gusts, visibility, UV index, solar radiation
- Today: max/min temperature, precipitation, chance of precipitation, max UV index, sunshine, sunrise, sunset
- Next hour: precipitation
- Air quality: European AQI, PM2.5, PM10, and alder, birch, grass and mugwort pollen

**Sensors disabled by default (enable them in the entity list):**
- Weather description (current and today)
- Rain, showers, snowfall and snow depth
- Low, mid and high cloud
- Surface pressure
- Wind at 80 m
- Radiation components
- CAPE, lifted index and convective inhibition
- Freezing level and boundary layer height
- Vapour pressure deficit and evapotranspiration
- Soil temperature and moisture (4-5 depths)
- Moonrise, moonset and moon phase
- Daylight duration
- AQI sub-indices, US AQI, NO₂, O₃, SO₂, CO, CO₂, dust, ammonia, methane, aerosol optical depth
- Olive and ragweed pollen

## Fair use and attribution

The free Open-Meteo API is for **non-commercial use**. The limit is 10,000 calls a day, 5,000 an hour and 600 a minute. One location with air quality uses roughly 1,000 calls a day: Open-Meteo counts a request with many variables as more than one call.

Data is from [Open-Meteo.com](https://open-meteo.com), licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Air quality data is from Copernicus Atmosphere Monitoring Service (CAMS) via Open-Meteo.

Built on [aioopenmeteo](https://github.com/briis/aioopenmeteo).
