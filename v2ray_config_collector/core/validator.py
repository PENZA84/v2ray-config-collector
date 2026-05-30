name: "🚀 Завод: Полный Цикл Производства Конфигов"

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

jobs:
  production:
    runs-on: ubuntu-latest
    steps:
      - name: "📥 Клонирование Репозитория"
        uses: actions/checkout@v4

      - name: "🐍 Установка Python"
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: "📦 Установка зависимостей"
        run: |
          python -m pip install --upgrade pip
          pip install requests pyyaml beautifulsoup4 tqdm playwright PySocks
          playwright install-deps chromium
          playwright install chromium

      - name: "🔍 Этап 1: Сбор Сырья (Scraping)"
        run: |
          python scrapers/v2ray_scraper.py

      - name: "🧹 Этап 2: Очистка и Дедупликация"
        run: |
          python processors/deduplicator.py

      - name: "⚡ Этап 3: Валидация (Connectivity Check)"
        run: |
          python validators/connectivity_validator.py

      - name: "💾 Этап 4: Фиксация Результатов (Git Commit)"
        run: |
          git config --global user.name "GitHub Actions Bot"
          git config --global user.email "actions@github.com"
          git add .
          # Если изменений нет, git commit вернет ошибку, поэтому используем || true
          git commit -m "🤖 Автоматическое обновление конфигов: $[ github.run_number ]" || echo "Изменений нет"
          git push origin main
