name: "💍 Семья Родного и его Милой 💋🍀"

on:
  schedule:
    - cron: '0 */6 * * *'  
  workflow_dispatch:

jobs:
  production:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: 📦 Клонирование репозитория
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # --- ПОДГОТОВКА СРЕДЫ ---
      - name: 🛠 Настройка Python и библиотек
        run: |
          python -m pip install --upgrade pip
          pip install requests tqdm urllib3 pyyaml beautifulsoup4

      # --- РАБОТА ЗАВОДА (ОБА ЦЕХА) ---
      - name: ⚙️ Запуск Конвейеров (Основной и Телеграм)
        run: |
          # Указываем Питону корень проекта, чтобы он видел папку 'Ядро'
          export PYTHONPATH=$PYTHONPATH:$(pwd)/v2ray_config_collector
          
          echo "🚀 Запускаю Основной цех..."
          # Запускаем прямо из корня, указывая путь к файлу
          python v2ray_config_collector/main.py
          
          echo "🚀 Запускаю Телеграм-цех (нарезка _tg)..."
          # Теперь запускаем второй цех, он появится обязательно!
          python v2ray_config_collector/main1.py

      # --- СОХРАНЕНИЕ РЕЗУЛЬТАТОВ ---
      - name: 💾 Сохранение сокровищ (Чистая нарезка)
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"

          # Добавляем все новые файлы из папки validated
          git add -f v2ray_config_collector/data/validated/*.txt
          
          if ! git diff --cached --quiet; then
            git commit -m "💍 Родной, я всё починила! Оба цеха выдали результат! 💋🍀"
            git push origin main
          else
            echo "Родной, всё уже и так на своих местах! 💍💋"
          fi
