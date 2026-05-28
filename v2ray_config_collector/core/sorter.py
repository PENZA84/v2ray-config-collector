import os
import re

class CountrySorter:
    def __init__(self):
        # Базовая папка проекта
        self.base_dir = "v2ray_config_collector"
        
        # Папка, где будут лежать файлы стран для Н
        self.output_dir = os.path.join(self.base_dir, "countries")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Протоколы для Трона (пропускаем их, они собираются в папке уникальных данных)
        self.proxy_protocols = re.compile(r'^(socks[45]?|https?|ssh)://', re.IGNORECASE)
        
        # Протоколы для Н (vless, vmess, trojan, ss и т.д.) — раскладываем по странам
        self.v2ray_protocols = re.compile(r'^(vless|vmess|trojan|ss|ssr|tuic|hysteria[2]?|v2ray)://', re.IGNORECASE)

    def sort_line(self, line):
        """
        Четкая сортировка одной строки по правилам Завода для Н и Трона.
        """
        clean_line = line.strip()
        if not clean_line or "://" not in clean_line:
            return None, None

        # 1. Если это прокси для Трона — просто пропускаем
        if self.proxy_protocols.match(clean_line):
            return None, None

        # 2. Если это конфиг для Н — отправляем в файл нужной страны
        if self.v2ray_protocols.match(clean_line):
            match = re.search(r'#([A-Z]{2})(?:_|$)', clean_line)
            if match:
                country_code = match.group(1).upper()
                file_name = f"{country_code}.txt"
            else:
                file_name = "UNKNOWN.txt"
                
            return os.path.join(self.output_dir, file_name), clean_line

        return None, None

    def find_input_file(self, default_path):
        """
        Умный поиск сырого файла по разным цехам Завода, если дефолтный путь пуст.
        """
        # Список возможных путей для проверки
        possible_paths = [
            default_path,
            "raw_configs.txt",
            os.path.join(self.base_dir, "raw_configs.txt"),
            "v2ray_config_collector/data/raw_configs.txt",
            "data/raw/raw_configs.txt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                return path
                
        return None

    def process_raw_data(self, default_input_path):
        """
        Чтение сырого файла, автопоиск путей и чистая сортировка только для Н
        """
        # Ищем, в какой цех парсер положил свежее топливо
        input_file_path = self.find_input_file(default_input_path)
        
        if not input_file_path:
            print(f"⚠️ Скрипт обошел все цеха, но файл с сырыми конфигами не найден.")
            print("📁 Вот что сейчас находится в текущей рабочей директории экшена:")
            for root, dirs, files in os.walk("."):
                # Показываем структуру папок, глубоко не зарываясь
                level = root.replace(".", "").count(os.sep)
                if level < 3:
                    indent = " " * 4 * level
                    print(f"{indent}📂 {os.path.basename(root)}/")
                    for f in files:
                        print(f"{indent}    📄 {f}")
            return

        print(f"🏭 Сортировщик успешно зашел в цех: {input_file_path}...")
        file_buffers = {}

        with open(input_file_path, "r", encoding="utf-8") as f:
            for line in f:
                target_file, sorted_line = self.sort_line(line)
                if target_file and sorted_line:
                    if target_file not in file_buffers:
                        file_buffers[target_file] = set()
                    file_buffers[target_file].add(sorted_line)

        # Записываем отфильтрованные данные v2ray по странам
        for file_path, lines in file_buffers.items():
            existing_lines = set()
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_lines = set(l.strip() for l in f if l.strip())
            
            all_lines = sorted(list(existing_lines.union(lines)))

            with open(file_path, "w", encoding="utf-8") as f:
                for l in all_lines:
                    f.write(l + "\n")
                    
        print(f"✅ Чистая сортировка для Н на основе {input_file_path} успешно завершена!")

if __name__ == "__main__":
    sorter = CountrySorter()
    # Стартовый дефолтный путь
    sorter.process_raw_data("v2ray_config_collector/data/raw/raw_configs.txt")
