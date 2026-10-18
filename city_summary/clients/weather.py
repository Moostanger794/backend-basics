import math

from clients.http import APIResponseError, get_json


class CityNotFoundError(Exception):
    pass


WEATHER_DESCRIPTIONS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    80: "rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


def is_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def get_weather(city: str) -> dict[str, float | str]:
    geo_data = get_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en"},
    )

    results = geo_data.get("results")

    if results is None:
        generation_time = geo_data.get("generationtime_ms")

        if is_number(generation_time) and generation_time >= 0:
            raise CityNotFoundError(f"Город не найден: {city}")

        raise APIResponseError(None, "Некорректный ответ геокодинга")

    if not isinstance(results, list):
        raise APIResponseError(None, "Некорректный список городов")

    if not results:
        raise CityNotFoundError(f"Город не найден: {city}")

    if not isinstance(results[0], dict):
        raise APIResponseError(None, "Некорректные данные города")

    location = results[0]
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if (
        not is_number(latitude)
        or not is_number(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        raise APIResponseError(None, "Некорректные координаты города")

    weather_data = get_json(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code",
        },
    )

    current = weather_data.get("current")

    if not isinstance(current, dict):
        raise APIResponseError(None, "Отсутствуют текущие погодные данные")

    temperature = current.get("temperature_2m")
    weather_code = current.get("weather_code")

    if not is_number(temperature):
        raise APIResponseError(None, "Некорректная температура")

    if isinstance(weather_code, bool) or not isinstance(weather_code, int):
        raise APIResponseError(None, "Некорректный код погоды")

    description = WEATHER_DESCRIPTIONS.get(weather_code, f"weather code {weather_code}")

    return {
        "temp_c": float(temperature),
        "description": description,
    }
