name: производство

on:
  push:
    branches: [ main, master ]
  schedule:
    - cron: '*/30 * * * *'
  workflow_dispatch:

jobs:
  базовый_цех:
    runs-on: ubuntu-latest
    steps:
      - name: Установка Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 24

      - name: Установка Python
        uses: actions/setup-python@v6
        with:
          python-version: '3.12'

      - name: Копируем код
        uses: actions/checkout@v5

      - name: Установка зависимостей
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml beautifulsoup4

      - name: Запуск сбора
        run: python v2ray_config_collector/main.py

      - name: Сохранение результатов
        uses: actions/upload-artifact@v5
        with:
          name: результаты
          path: data/unique/
