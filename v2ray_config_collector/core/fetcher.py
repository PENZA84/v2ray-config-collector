import os
import requests
import re
import base64
import urllib3

# Тишина в доме — залог спокойствия
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ConfigFetcher:
    def __init__(self):
        # Определяем пути к твоим полочкам
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_path, 'data', 'sources')
        
        # Твои два главных склада
        self.main_storage = os.path.join(self.data_dir, 'sources.txt')   # ОСНОВНОЙ (сайты, RAW)
        self.tg_storage = os.path.join(self.data_dir, 'sources1.txt')   # ТЕЛЕГРАМ / БЫСТРЫЕ
        
        os.makedirs(self.data_dir, exist_ok=True)
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

    def sort_and_save(self, link):
        """Метод, который отвечает за раскладку по полочкам"""
        link = link.strip()
        if not link: return

        # Правило для Телеграма — на полочку sources1.txt
        if "t.me" in link or "telegram.me" in link:
            target = self.tg_storage
            label = "📱 Телеграм"
        # Все остальное (RAW, GitHub, сайты) — на основную полочку sources.txt
        else:
            target = self.main_storage
            label = "🌐 Основной"

        # Проверяем, нет ли уже такой ссылки, чтобы не дублировать
        existing = []
        if os.path.exists(target):
            with open(target, 'r', encoding='utf-8') as f:
                existing = f.read().splitlines()

        if link not in existing:
            with open(target, 'a', encoding='utf-8') as f:
                f.write(link + "\n")
            print(f"✅ {label} разложен: {link}")

    def fetch_all(self):
        """Основной процесс сбора и анализа"""
        print(f"🏗️ ЗАВОД PENZA84: Начинаю глубокую сортировку...")
        
        # Здесь логика обхода твоих 5000+ ссылок из существующих файлов
        # Если в процессе обхода (например, в README) находится новая ссылка:
        # Мы вызываем self.sort_and_save(new_link)
        
        # Пример работы (имитация нахождения ссылок в README):
        found_in_readme = [
            "https://t.me/new_proxy_channel",
            "https://raw.githubusercontent.com/user/config/main/sub.txt"
        ]
        
        for found_link in found_in_readme:
            self.sort_and_save(found_link)

    def _decode_if_base64(self, data):
        """Магия декодирования для 'мяса' конфигов"""
        try:
            s = data.strip()
            s += '=' * (-len(s) % 4)
            return base64.b64decode(s).decode('utf-8')
        except:
            return data

if
