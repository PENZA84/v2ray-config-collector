import requests
import os

class SourceCollector:
    def __init__(self, source_file=None, output_file=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Твой огромный список на 10к строк
        self.source_file = source_file or os.path.join(package_dir, 'data', 'sources', 'sources.txt')
        # Куда складываем сырые конфиги
        self.output_file = output_file or os.path.join(package_dir, 'data', 'raw', 'raw_configs.txt')

    def fetch_all_configs(self):
        if not os.path.exists(self.source_file):
            print("Источники не найдены!")
            return

        with open(self.source_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"Начинаю проверку и сбор. Ссылок в плане: {len(urls)}")
        
        all_content = []
        working_urls = [] # Сюда попадут только те, кто не 404

        for url in urls:
            # Пропускаем комментарии, но сохраняем их в рабочем списке
            if url.startswith('#'):
                working_urls.append(url)
                continue

            try:
                # Пробуем достучаться
                response = requests.get(url, timeout=10, allow_redirects=True)
                
                if response.status_code == 200:
                    all_content.append(response.text)
                    working_urls.append(url) # Ссылка живая, оставляем!
                elif response.status_code == 404:
                    print(f"🗑 Удаляю мертвую ссылку (404): {url}")
                    # Просто НЕ добавляем её в working_urls
                else:
                    # Если ошибка временная (например, 429 или 500), пока оставим
                    print(f"Временная проблема ({response.status_code}), оставляю: {url}")
                    working_urls.append(url)
            
            except Exception:
                print(f"⚠️ Ошибка сети, оставляю на всякий случай: {url}")
                working_urls.append(url)

        # --- МАГИЯ ОЧИСТКИ ---
        # Перезаписываем твой sources.txt только живыми ссылками!
        with open(self.source_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(working_urls))

        # Сохраняем добытое "сырьё"
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
            
        print(f"--- Чистка завершена! ---")
        print(f"Осталось живых ссылок: {len(working_urls)}")
        print(f"Сырые данные сохранены в: {self.output_file}")
