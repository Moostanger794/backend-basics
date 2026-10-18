
# City Summary

CLI-утилита для получения погоды в выбранном городе и курса валюты к рублю.

## Требования

- Python 3.12
- Интернет-соединение

## Установка

Создать виртуальное окружение:

```powershell
py -3.12 -m venv .venv
```

Активировать окружение (Windows PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Установить зависимости:

```powershell
python -m pip install -r requirements.txt
```

## Запуск

Запуск с валютой по умолчанию (USD):

```powershell
python main.py --city Moscow
```

Выбор другой валюты:

```powershell
python main.py --city Moscow --currency EUR
```

Вывод в формате JSON:

```powershell
python main.py --city Moscow --json
```

Справка:

```powershell
python main.py --help
```

## Используемые API

- Open-Meteo — геокодинг города и получение текущей погоды.
- Frankfurter — получение курса валюты к RUB.

API-ключи не требуются.

## Обработка данных

- warm_clothes = true, если температура ниже 0°C.
- expensive = true, если курс валюты выше 100 RUB.

## Коды завершения

- 0 — успешное выполнение.
- 2 — ошибка аргументов.
- 3 — город или валюта не найдены.
- 4 — ошибка внешнего API.

## Проверка кода

```powershell
ruff check .
ruff format .
```

## Тестирование

```powershell
python -m unittest discover -s tests -v
```

Тесты проверяют HTTP-запросы, timeout, retry, валидацию ответов API, обработку данных и CLI.

## Структура

- clients/ — HTTP-запросы и работа с внешними API.
- processing/ — предобработка данных и сборка сводки.
- main.py — аргументы командной строки и вывод результата.
- tests/ — автоматические тесты.
