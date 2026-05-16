- name: 💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          
          # Создаем правильную структуру папок в корне репозитория
          mkdir -p data/validated
          
          # Копируем сгенерированный файл из рабочего каталога в корень для Git
          cp "v2ray_config_collector/data/validated/validated_configs.txt" "data/validated/validated_configs.txt" || true
          
          # Добавляем файлы в отслеживание Git
          git add data/
          git commit -m "⏳ База обновлена! Ядро Sing-Box отфильтровало дубли." || echo "Нет изменений для коммита"
          git push
