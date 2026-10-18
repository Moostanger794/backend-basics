import math
import re
from datetime import date

from clients.http import APIResponseError, get_json


class CurrencyNotFoundError(Exception):
    pass


def get_rate(currency: str) -> float:
    currency = currency.upper()

    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise CurrencyNotFoundError(f"Некорректный код валюты: {currency}")

    try:
        data = get_json(f"https://api.frankfurter.dev/v2/rate/{currency}/RUB")
    except APIResponseError as exc:
        if exc.status_code in (404, 422):
            raise CurrencyNotFoundError(f"Валюта не найдена: {currency}") from exc
        raise

    if data.get("base") != currency or data.get("quote") != "RUB":
        raise APIResponseError(None, "Некорректная валютная пара")

    rate = data.get("rate")

    if (
        isinstance(rate, bool)
        or not isinstance(rate, (int, float))
        or not math.isfinite(rate)
        or rate <= 0
    ):
        raise APIResponseError(None, "Некорректное значение курса")

    rate_date = data.get("date")

    if not isinstance(rate_date, str):
        raise APIResponseError(None, "Отсутствует дата курса")

    try:
        date.fromisoformat(rate_date)
    except ValueError as exc:
        raise APIResponseError(None, "Некорректная дата курса") from exc

    return float(rate)
