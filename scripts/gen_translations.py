"""Generate strings.json and translations/{en,da}.json for openmeteo_weather.

Run from the repo root: python scripts/gen_translations.py
Edit the tables below, not the generated JSON files.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "openmeteo_weather"

# key: (English, Danish)
SENSORS: dict[str, tuple[str, str]] = {
    "temperature": ("Temperature", "Temperatur"),
    "apparent_temperature": ("Feels like", "Føles som"),
    "dew_point": ("Dew point", "Dugpunkt"),
    "wet_bulb_temperature": ("Wet bulb temperature", "Vådtemperatur"),
    "humidity": ("Humidity", "Luftfugtighed"),
    "weather": ("Weather", "Vejr"),
    "precipitation": ("Precipitation", "Nedbør"),
    "precipitation_probability": ("Chance of precipitation", "Sandsynlighed for nedbør"),
    "rain": ("Rain", "Regn"),
    "showers": ("Showers", "Byger"),
    "snowfall": ("Snowfall", "Snefald"),
    "snow_depth": ("Snow depth", "Snedybde"),
    "cloud_cover": ("Cloud cover", "Skydække"),
    "cloud_cover_low": ("Low cloud cover", "Lavt skydække"),
    "cloud_cover_mid": ("Mid cloud cover", "Mellemhøjt skydække"),
    "cloud_cover_high": ("High cloud cover", "Højt skydække"),
    "pressure": ("Pressure", "Lufttryk"),
    "surface_pressure": ("Surface pressure", "Lufttryk ved jorden"),
    "wind_speed": ("Wind speed", "Vindhastighed"),
    "wind_direction": ("Wind direction", "Vindretning"),
    "wind_gusts": ("Wind gusts", "Vindstød"),
    "wind_speed_80m": ("Wind speed (80 m)", "Vindhastighed (80 m)"),
    "wind_direction_80m": ("Wind direction (80 m)", "Vindretning (80 m)"),
    "visibility": ("Visibility", "Sigtbarhed"),
    "uv_index": ("UV index", "UV-indeks"),
    "uv_index_clear_sky": ("UV index, clear sky", "UV-indeks, skyfri himmel"),
    "solar_radiation": ("Solar radiation", "Solindstråling"),
    "direct_radiation": ("Direct radiation", "Direkte stråling"),
    "diffuse_radiation": ("Diffuse radiation", "Diffus stråling"),
    "direct_normal_irradiance": ("Direct normal irradiance", "Direkte normalindstråling"),
    "terrestrial_radiation": ("Terrestrial radiation", "Stråling uden for atmosfæren"),
    "sunshine_duration": ("Sunshine (last 15 min)", "Solskin (seneste 15 min)"),
    "cape": ("CAPE", "CAPE"),
    "lifted_index": ("Lifted index", "Lifted index"),
    "convective_inhibition": ("Convective inhibition", "Konvektiv hæmning"),
    "freezing_level_height": ("Freezing level", "Frysepunktshøjde"),
    "boundary_layer_height": ("Boundary layer height", "Grænselagshøjde"),
    "vapour_pressure_deficit": ("Vapour pressure deficit", "Damptryksunderskud"),
    "evapotranspiration": ("Evapotranspiration", "Fordampning"),
    "et0_fao_evapotranspiration": (
        "Reference evapotranspiration",
        "Referencefordampning",
    ),
    "total_column_integrated_water_vapour": ("Water vapour column", "Vanddamp i luftsøjlen"),
    "soil_temperature_0cm": ("Soil temperature (0 cm)", "Jordtemperatur (0 cm)"),
    "soil_temperature_6cm": ("Soil temperature (6 cm)", "Jordtemperatur (6 cm)"),
    "soil_temperature_18cm": ("Soil temperature (18 cm)", "Jordtemperatur (18 cm)"),
    "soil_temperature_54cm": ("Soil temperature (54 cm)", "Jordtemperatur (54 cm)"),
    "soil_moisture_0_to_1cm": ("Soil moisture (0-1 cm)", "Jordfugtighed (0-1 cm)"),
    "soil_moisture_1_to_3cm": ("Soil moisture (1-3 cm)", "Jordfugtighed (1-3 cm)"),
    "soil_moisture_3_to_9cm": ("Soil moisture (3-9 cm)", "Jordfugtighed (3-9 cm)"),
    "soil_moisture_9_to_27cm": ("Soil moisture (9-27 cm)", "Jordfugtighed (9-27 cm)"),
    "soil_moisture_27_to_81cm": ("Soil moisture (27-81 cm)", "Jordfugtighed (27-81 cm)"),
    "today_weather": ("Weather today", "Vejret i dag"),
    "today_temperature_max": ("Max temperature today", "Højeste temperatur i dag"),
    "today_temperature_min": ("Min temperature today", "Laveste temperatur i dag"),
    "today_apparent_temperature_max": ("Max feels like today", "Højeste føles som i dag"),
    "today_apparent_temperature_min": ("Min feels like today", "Laveste føles som i dag"),
    "today_precipitation_sum": ("Precipitation today", "Nedbør i dag"),
    "today_rain_sum": ("Rain today", "Regn i dag"),
    "today_showers_sum": ("Showers today", "Byger i dag"),
    "today_snowfall_sum": ("Snowfall today", "Snefald i dag"),
    "today_precipitation_hours": ("Hours with precipitation today", "Timer med nedbør i dag"),
    "today_precipitation_probability_max": (
        "Chance of precipitation today",
        "Sandsynlighed for nedbør i dag",
    ),
    "today_wind_speed_10m_max": ("Max wind speed today", "Højeste vindhastighed i dag"),
    "today_wind_gusts_10m_max": ("Max wind gusts today", "Kraftigste vindstød i dag"),
    "today_wind_direction_10m_dominant": (
        "Dominant wind direction today",
        "Fremherskende vindretning i dag",
    ),
    "today_uv_index_max": ("Max UV index today", "Højeste UV-indeks i dag"),
    "today_sunshine_duration": ("Sunshine today", "Solskinstimer i dag"),
    "today_daylight_duration": ("Daylight today", "Dagslys i dag"),
    "today_shortwave_radiation_sum": ("Solar energy today", "Solenergi i dag"),
    "today_et0_fao_evapotranspiration": (
        "Reference evapotranspiration today",
        "Referencefordampning i dag",
    ),
    "sunrise": ("Sunrise", "Solopgang"),
    "sunset": ("Sunset", "Solnedgang"),
    "moonrise": ("Moonrise", "Måneopgang"),
    "moonset": ("Moonset", "Månenedgang"),
    "moon_phase": ("Moon phase", "Månefase"),
    "precipitation_next_hour": ("Precipitation next hour", "Nedbør næste time"),
    "wind_gusts_next_hour": ("Max wind gusts next hour", "Kraftigste vindstød næste time"),
    "lightning_potential_next_hour": ("Lightning potential next hour", "Lynpotentiale næste time"),
    "european_aqi": ("European AQI", "Europæisk luftkvalitetsindeks"),
    "european_aqi_pm2_5": ("European AQI PM2.5", "Europæisk luftkvalitetsindeks PM2.5"),
    "european_aqi_pm10": ("European AQI PM10", "Europæisk luftkvalitetsindeks PM10"),
    "european_aqi_nitrogen_dioxide": (
        "European AQI nitrogen dioxide",
        "Europæisk luftkvalitetsindeks kvælstofdioxid",
    ),
    "european_aqi_ozone": ("European AQI ozone", "Europæisk luftkvalitetsindeks ozon"),
    "european_aqi_sulphur_dioxide": (
        "European AQI sulphur dioxide",
        "Europæisk luftkvalitetsindeks svovldioxid",
    ),
    "us_aqi": ("US AQI", "Amerikansk luftkvalitetsindeks"),
    "pm2_5": ("PM2.5", "PM2.5"),
    "pm10": ("PM10", "PM10"),
    "nitrogen_dioxide": ("Nitrogen dioxide", "Kvælstofdioxid"),
    "ozone": ("Ozone", "Ozon"),
    "sulphur_dioxide": ("Sulphur dioxide", "Svovldioxid"),
    "carbon_monoxide": ("Carbon monoxide", "Kulilte"),
    "carbon_dioxide": ("Carbon dioxide", "Kuldioxid"),
    "dust": ("Dust", "Støv"),
    "ammonia": ("Ammonia", "Ammoniak"),
    "methane": ("Methane", "Metan"),
    "aerosol_optical_depth": ("Aerosol optical depth", "Aerosol optisk dybde"),
    "alder_pollen": ("Alder pollen", "Ellepollen"),
    "birch_pollen": ("Birch pollen", "Birkepollen"),
    "grass_pollen": ("Grass pollen", "Græspollen"),
    "mugwort_pollen": ("Mugwort pollen", "Bynkepollen"),
    "olive_pollen": ("Olive pollen", "Olivenpollen"),
    "ragweed_pollen": ("Ragweed pollen", "Ambrosiapollen"),
}

WEATHER_STATES: dict[str, tuple[str, str]] = {
    "clear_sky": ("Clear sky", "Skyfrit"),
    "mainly_clear": ("Mainly clear", "Overvejende skyfrit"),
    "partly_cloudy": ("Partly cloudy", "Delvis skyet"),
    "overcast": ("Overcast", "Overskyet"),
    "fog": ("Fog", "Tåge"),
    "depositing_rime_fog": ("Freezing fog", "Rimtåge"),
    "drizzle_light": ("Light drizzle", "Let støvregn"),
    "drizzle_moderate": ("Drizzle", "Støvregn"),
    "drizzle_dense": ("Dense drizzle", "Tæt støvregn"),
    "freezing_drizzle_light": ("Light freezing drizzle", "Let isslag"),
    "freezing_drizzle_dense": ("Dense freezing drizzle", "Kraftig isslag"),
    "rain_slight": ("Light rain", "Let regn"),
    "rain_moderate": ("Rain", "Regn"),
    "rain_heavy": ("Heavy rain", "Kraftig regn"),
    "freezing_rain_light": ("Light freezing rain", "Let underafkølet regn"),
    "freezing_rain_heavy": ("Heavy freezing rain", "Kraftig underafkølet regn"),
    "snow_slight": ("Light snow", "Let sne"),
    "snow_moderate": ("Snow", "Sne"),
    "snow_heavy": ("Heavy snow", "Kraftigt snefald"),
    "snow_grains": ("Snow grains", "Kornsne"),
    "rain_showers_slight": ("Light rain showers", "Lette regnbyger"),
    "rain_showers_moderate": ("Rain showers", "Regnbyger"),
    "rain_showers_violent": ("Violent rain showers", "Kraftige regnbyger"),
    "snow_showers_slight": ("Light snow showers", "Lette snebyger"),
    "snow_showers_heavy": ("Heavy snow showers", "Kraftige snebyger"),
    "thunderstorm": ("Thunderstorm", "Torden"),
    "thunderstorm_slight_hail": ("Thunderstorm with hail", "Torden med hagl"),
    "thunderstorm_heavy_hail": ("Thunderstorm with heavy hail", "Torden med kraftige hagl"),
}

MOON_STATES: dict[str, tuple[str, str]] = {
    "new_moon": ("New moon", "Nymåne"),
    "waxing_crescent": ("Waxing crescent", "Tiltagende måne"),
    "first_quarter": ("First quarter", "Første kvarter"),
    "waxing_gibbous": ("Waxing gibbous", "Tiltagende fuldmåne"),
    "full_moon": ("Full moon", "Fuldmåne"),
    "waning_gibbous": ("Waning gibbous", "Aftagende fuldmåne"),
    "last_quarter": ("Last quarter", "Sidste kvarter"),
    "waning_crescent": ("Waning crescent", "Aftagende måne"),
}

SETTINGS = {
    "en": {
        "data": {
            "model": "Weather model",
            "air_quality": "Air quality and pollen",
            "forecast_days": "Forecast days",
            "minutely_15": "15-minute data",
        },
        "data_description": {
            "model": "Best match combines the best models for your location. "
            "Regional models only work inside their area.",
            "air_quality": "Air quality index, particles, gases and pollen from CAMS, every hour",
            "forecast_days": "Length of the daily and hourly forecast (1-16 days)",
            "minutely_15": "Used for precipitation and gusts in the next hour. "
            "Native in Central Europe and North America, interpolated elsewhere.",
        },
    },
    "da": {
        "data": {
            "model": "Vejrmodel",
            "air_quality": "Luftkvalitet og pollen",
            "forecast_days": "Prognosedage",
            "minutely_15": "Data for hvert kvarter",
        },
        "data_description": {
            "model": "Best match kombinerer de bedste modeller for din placering. "
            "Regionale modeller virker kun inden for deres område.",
            "air_quality": "Luftkvalitetsindeks, partikler, gasser og pollen fra CAMS, hver time",
            "forecast_days": "Længden af dags- og timeprognosen (1-16 dage)",
            "minutely_15": "Bruges til nedbør og vindstød i den næste time. "
            "Rigtige kvartersdata i Centraleuropa og Nordamerika, interpoleret andre steder.",
        },
    },
}

TEXT = {
    "en": {
        "title": "Open-Meteo Weather",
        "description": "Forecast from Open-Meteo.com, free for non-commercial use. "
        "Data: Open-Meteo.com, CC BY 4.0.",
        "name": "Name",
        "location": "Location",
        "location_desc": "The point to forecast for",
        "options_title": "Open-Meteo settings",
        "options_description": "Changing the model replaces sensors the new model "
        "does not provide.",
        "errors": {
            "cannot_connect": "Could not connect to Open-Meteo",
            "rate_limited": "Open-Meteo's free limit has been reached, try again later",
            "unknown": "Unexpected answer from Open-Meteo",
            "model_not_available": "This model has no data for the location",
            "model_already_configured": "This location is already set up with this model",
        },
        "already_configured": "This location is already set up with this model",
    },
    "da": {
        "title": "Open-Meteo Vejr",
        "description": "Prognose fra Open-Meteo.com, gratis til ikke-kommerciel brug. "
        "Data: Open-Meteo.com, CC BY 4.0.",
        "name": "Navn",
        "location": "Placering",
        "location_desc": "Punktet der skal laves prognose for",
        "options_title": "Open-Meteo indstillinger",
        "options_description": "Skifter du model, erstattes sensorer som den nye "
        "model ikke leverer.",
        "errors": {
            "cannot_connect": "Kunne ikke forbinde til Open-Meteo",
            "rate_limited": "Open-Meteos gratis grænse er nået, prøv igen senere",
            "unknown": "Uventet svar fra Open-Meteo",
            "model_not_available": "Modellen har ingen data for placeringen",
            "model_already_configured": "Placeringen er allerede sat op med denne model",
        },
        "already_configured": "Placeringen er allerede sat op med denne model",
    },
}


def build(lang: str) -> dict:
    i = 0 if lang == "en" else 1
    t = TEXT[lang]
    s = SETTINGS[lang]
    sensors: dict[str, dict] = {}
    for key, names in SENSORS.items():
        sensors[key] = {"name": names[i]}
    for key in ("weather", "today_weather"):
        sensors[key]["state"] = {k: v[i] for k, v in WEATHER_STATES.items()}
    sensors["moon_phase"]["state"] = {k: v[i] for k, v in MOON_STATES.items()}
    return {
        "config": {
            "step": {
                "user": {
                    "title": t["title"],
                    "description": t["description"],
                    "data": {"name": t["name"], "location": t["location"], **s["data"]},
                    "data_description": {"location": t["location_desc"], **s["data_description"]},
                }
            },
            "error": t["errors"],
            "abort": {"already_configured": t["already_configured"]},
        },
        "options": {
            "step": {
                "init": {
                    "title": t["options_title"],
                    "description": t["options_description"],
                    "data": s["data"],
                    "data_description": s["data_description"],
                }
            },
            "error": t["errors"],
        },
        "entity": {"sensor": sensors},
    }


def main() -> None:
    (ROOT / "translations").mkdir(exist_ok=True)
    for lang in ("en", "da"):
        text = json.dumps(build(lang), indent=2, ensure_ascii=False) + "\n"
        (ROOT / "translations" / f"{lang}.json").write_text(text, encoding="utf-8")
        if lang == "en":
            (ROOT / "strings.json").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
