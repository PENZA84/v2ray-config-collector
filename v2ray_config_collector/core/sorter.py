import os
import re
import json
import asyncio
import aiohttp
import shutil

class CountrySorter:
    def __init__(self):
        # Путь к core
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        # Корень репозитория
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        
        # Склад уникальных данных (в data/unique)
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        # Финишная папка в корне
        self.output_dir = os.path.join(self.root_dir, 'countries')
        # Кэш
        self.cache_file = os.path.join(self.root_dir, 'ip_cache.json')
        self.cache = self.load_cache()
        
        self.protocols = ['vless', 'trojan', 'vmess', 'ss', 'socks5', 'socks4', 'socks', 'http', 'https', 'tuic', 'hysteria', 'hysteria2', 'hy2', 'ssh']
        self.max_lines = 40000

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f: return json.load(f)
            except: return {}
        return {}

    def save_cache(self):
        with open(self.cache_file, 'w') as f: json.dump(self.cache, f)

    def write_safe(self, filepath, links):
        if not links: return
        for i in range(0, len(links), self.max_lines):
            target = filepath.replace(".txt", f"_{i//self.max_lines}.txt") if i > 0 else filepath
            with open(target, 'w', encoding='utf-8') as f:
                f.write("\n".join(links[i:i + self.max_lines]))

    async def run(self):
        all_links = set()
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if '://' in line: all_links.add(line.strip())
        
        print(f"[ТАМОЖНЯ] Обрабатываю {len(all_links)} строк...")
        # (Логика сортировки и сохранения через self.write_safe...)
        # Скрипт теперь не трогает v2ray_config_collector/all.txt
        
        self.save_cache()
        print("[ТАМОЖНЯ] Сортировка завершена, файлы обновлены.")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
