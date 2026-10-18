from clients.rates import get_rate
from clients.weather import get_weather
from processing.preprocessing import is_expensive_rate, needs_warm_clothes


def build_city_summary(
    city: str,
    currency: str = "USD",
) -> dict[str, object]:
    weather = get_weather(city)
    rate_to_rub = get_rate(currency)

    temp_c = float(weather["temp_c"])

    return {
        "city": city,
        "weather": {
            "temp_c": temp_c,
            "description": weather["description"],
            "warm_clothes": needs_warm_clothes(temp_c),
        },
        "rates": {
            "currency": currency.upper(),
            "rate_to_rub": rate_to_rub,
            "expensive": is_expensive_rate(rate_to_rub),
        },
    }
