import math
import time

import requests

TIMEOUT = 10
MAX_ATTEMPTS = 3
RETRY_STATUSES = {429, 500, 502, 503, 504}


class APIUnavailableError(Exception):
    pass


class APIResponseError(Exception):
    def __init__(self, status_code: int | None, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


def retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None and response.status_code == 429:
        retry_after = response.headers.get("Retry-After")

        if retry_after is not None:
            try:
                seconds = float(retry_after)
                if math.isfinite(seconds) and seconds >= 0:
                    return seconds
            except ValueError:
                pass

    return float(attempt)


def get_json(
    url: str,
    params: dict[str, str | int | float] | None = None,
) -> dict[str, object]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = None

        try:
            response = requests.get(url, params=params, timeout=TIMEOUT)

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ) as exc:
            if attempt == MAX_ATTEMPTS:
                raise APIUnavailableError("Сервис недоступен после повторов") from exc

        else:
            if response.status_code in RETRY_STATUSES:
                if attempt == MAX_ATTEMPTS:
                    raise APIUnavailableError(
                        f"Сервис недоступен: HTTP {response.status_code}"
                    )

            elif response.status_code != 200:
                raise APIResponseError(
                    response.status_code,
                    f"Неожиданный HTTP-статус: {response.status_code}",
                )

            else:
                try:
                    data = response.json()
                except ValueError as exc:
                    raise APIResponseError(None, "Некорректный JSON") from exc

                if not isinstance(data, dict):
                    raise APIResponseError(None, "Ожидался JSON-объект")

                return data

        if attempt < MAX_ATTEMPTS:
            time.sleep(retry_delay(response, attempt))

    raise APIUnavailableError("Сервис недоступен")
