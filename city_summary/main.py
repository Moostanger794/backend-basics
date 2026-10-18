import argparse
import json
import sys

from clients.http import APIResponseError, APIUnavailableError
from clients.rates import CurrencyNotFoundError
from clients.weather import CityNotFoundError
from processing.service import build_city_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Сводка по городу: погода и курс валюты."
    )

    parser.add_argument(
        "--city",
        required=True,
        help="Название города, например Moscow",
    )

    parser.add_argument(
        "--currency",
        default="USD",
        help="Код валюты, по умолчанию USD",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Вывести сводку в формате JSON",
    )

    args = parser.parse_args()

    city = args.city.strip()
    currency = args.currency.upper()

    if not city:
        parser.error("Название города не может быть пустым")

    try:
        summary = build_city_summary(city, currency)

    except (CityNotFoundError, CurrencyNotFoundError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 3

    except (APIUnavailableError, APIResponseError) as exc:
        print(f"Ошибка внешнего API: {exc}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        weather = summary["weather"]
        rates = summary["rates"]

        print(f"Город: {summary['city']}")
        print(f"Погода: {weather['temp_c']}°C, {weather['description']}")
        print(f"Тёплая одежда: {'да' if weather['warm_clothes'] else 'нет'}")
        print(f"{rates['currency']}→RUB: {rates['rate_to_rub']:.2f}")
        print(f"Дорогой курс: {'да' if rates['expensive'] else 'нет'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
