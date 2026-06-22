name: "🧹 Чистильщик URLs 💋"

on:
  push:
    paths:
      - 'urls/source_urls.txt'
  schedule:
    - cron: '0 */12 * * *'
  workflow_dispatch:

jobs:
  run-cleaner:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: 📦 Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install aiohttp requests

      - name: 🌱 Prepare environment
        run: mkdir -p urls data/raw_incoming

      - name: 🔍 Process source_urls.txt
        run: python urls/source_cleaner_urls.py

      - name: 💾 Save dead links & Statistics
        run: |
          python <<EOF
          import os

          # === ДОКУМЕНТЫ ЗАВОДА ===
          filtered_file = 📄 "urls/filtered_results.txt" 📄
          factory_file   = 📄 "urls/factory_valid.txt" 📄
          checks_file    = 📄 "urls/url_checks.txt" 📄
          dead_file      = 📄 "data/raw_incoming/deep_raw_collected.txt" 📄

          print("📋 ════════════════════════════════════════ 📋")
          print("          📄   РЕЕСТР ДОКУМЕНТОВ ЗАВОДА   📄")
          print("═══════════════════════════════════════════════")

          factory_count = len([line for line in open(factory_file, encoding='utf-8') if line.strip()]) if os.path.exists(factory_file) else 0
          filtered_count = len([line for line in open(filtered_file, encoding='utf-8') if line.strip()]) if os.path.exists(filtered_file) else 0
          checks_count = len([line for line in open(checks_file, encoding='utf-8') if line.strip()]) if os.path.exists(checks_file) else 0

          existing_dead = set()
          if os.path.exists(dead_file):
              with open(dead_file, "r", encoding="utf-8") as f:
                  existing_dead = {line.strip() for line in f if line.strip() and not line.startswith('#')}

          new_dead = set()
          if os.path.exists(filtered_file):
              with open(filtered_file, "r", encoding="utf-8") as f:
                  for line in f:
                      line = line.strip()
                      if line and line.startswith('http'):
                          new_dead.add(line)

          all_dead = existing_dead.union(new_dead)
          os.makedirs(os.path.dirname(dead_file), exist_ok=True)
          
          with open(dead_file, "w", encoding="utf-8") as f:
              f.write("# БУНКЕР ОТХОДОВ\n\n")
              f.write("\n".join(sorted(all_dead)) + "\n")

          print(f"🏭 Factory     : {factory_count}")
          print(f"🗑  Filtered    : {filtered_count}")
          print(f"🔍  Url_checks  : {checks_count}")
          print(f"💀  Dead saved  : {len(all_dead)}")
          print("📋 ════════════════════════════════════════ 📋")
          EOF

      - name: 🚀 Commit & Push
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          
          git add urls/* data/raw_incoming/deep_raw_collected.txt
          
          if git diff --staged --quiet; then
            echo "✨ Нет изменений"
          else
            git commit -m "🧹 Чистильщик URLs: обновление списков 💋"
            git push
          fi
