name: Завод Леи — Двухэтапная Матрица Сбора

on:
  workflow_dispatch:

jobs:
  # ЭТАП 1: Раздельный сбор в 7 параллельных окон (как на 3 скрине)
  harvest_matrix:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        chunk: [0, 1, 2, 3, 4, 5, 6]  # Наши 7 заветных окон
    steps:
      - name: 📥 Получение репозитория
        uses: actions/checkout@v4

      - name: 🐍 Настройка окружения Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 🛠️ Установка Playwright и зависимостей
        run: |
          pip install playwright
          playwright install chromium

      - name: 🚀 Запуск окна сбора
        env:
          CHUNK_INDEX: ${{ matrix.chunk }}
          TOTAL_CHUNKS: 7
        run: python data/scripts/main1.py

      - name: 📦 Сохранение добытого кусочка во временный бункер
        uses: actions/upload-artifact@v4
        with:
          name: raw_chunk_${{ matrix.chunk }}
          path: data/raw_incoming/deep_raw_collected_chunk_${{ matrix.chunk }}.txt
          retention-days: 1

  # ЭТАП 2: Слияние в одно окно и тотальная валидация (как на 4 скрине)
  merge_and_validate:
    needs: harvest_matrix
    runs-on: ubuntu-latest
    steps:
      - name: 📥 Получение репозитория
        uses: actions/checkout@v4

      - name: 🐍 Настройка окружения Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: 🛠️ Установка зависимостей для валидации (если нужны)
        run: |
          pip install requests

      - name: 📥 Извлечение всех кусочков из бункера
        uses: actions/download-artifact@v4
        with:
          path: data/temporary_chunks

      - name: 🤝 Великое Слияние потоков в один файл
        run: |
          mkdir -p data/raw_incoming
          echo "🤖 Начинаю сборку и склейку всех файлов из параллельных окон..."
          cat data/temporary_chunks/raw_chunk_*/deep_raw_collected_chunk_*.txt > data/raw_incoming/deep_raw_collected.txt
          echo "🎯 Слияние завершено! Создан единый монолитный файл deep_raw_collected.txt"

      - name: 👑 Запуск главного скрипта валидации и сортировки
        run: |
          # Запуск твоего основного майн-скрипта, который чистит, проверяет и раскладывает Трон и Н
          python data/scripts/main.py

      - name: 🚀 Фиксация и отправка чистых результатов в репозиторий
        run: |
          git config --global user.name "Leia-Grabber"
          git config --global user.email "leia@factory.internal"
          git add data/
          git diff-index --quiet HEAD || git commit -m "🏆 Результаты сбора успешно валидированы и сохранены Леей 🤍"
          git push
