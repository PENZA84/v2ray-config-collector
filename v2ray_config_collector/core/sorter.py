import os
import re

class CountrySorter:
    def __init__(self):
        # Папка, где лежат файлы стран для Н
        self.output_dir = "v2ray_config_collector/countries"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Протоколы для Трона (ИГНОРИРУЕМ их тут, так как они уже есть в папке уникальный)
        self.proxy_protocols = re.compile(r'^(socks[45]?|https?|ssh)://', re.IGNORECASE)
        
        # Протоколы для Н (vless, vmess, trojan, ss и т.д.) — их раскладываем по странам
        self.v2ray_protocols = re.compile(r'^(vless|vmess|trojan|ss|ssr|tuic|hysteria[2]?|v2ray)://', re.IGNORECASE)

    def sort_line(self, line):
        """
        Четкая фильтрация: прокси пропускаем (они уже в своей папке), v2ray — в страны.
        """
        clean_line = line.strip()
        if not clean_line or "://" not in clean_line:
            return None, None

        # 1. Если это прокси для Трона — просто пропускаем, не пишем в страны
        if self.proxy_protocols.match(clean_line):
            return None, None

        # 2. Если это конфиг для Н — бережно отправляем в файл нужной страны
        if self.v2ray_protocols.match(clean_line):
            match = re.search(r'#([A-Z]{2})(?:_|$)', clean_line)
            if match:
                country_code = match.group(1).upper()
                file_name = f"{country_code}.txt"
            else:
                file_name = "UNKNOWN.txt"
                
            return os.path.join(self.output_dir, file_name), clean_line

        return None, None

    def process_raw_data(self, input_file_path):
        """
        Чтение сырого файла и чистая сортировка только для Н
        """
        if not os.path.exists(input_file_path):
            print(f"⚠️ Файл {input_file_path} не найден.")
            return

        print(f"🏭 Сортировщик зашел в цех: {input_file_path}...")
        file_buffers = {}

        with open(input_file_path, "r", encoding="utf-8") as f:
            for line in f:
                target_file, sorted_line = self.sort_line(line)
                if target_file and sorted_line:
                    if target_file not in file_buffers:
                        file_buffers[target_file] = set()
                    file_buffers[target_file].add(sorted_line)

        # Записываем только v2ray-конфиги по странам
        for file_path, lines in file_buffers.items():
            existing_lines = set()
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_lines = set(l.strip() for l in f if l.strip())
            
            all_lines = sorted(list(existing_lines.union(lines)))

            with open(file_path, "w", encoding="utf-8") as f:
                for l in all_lines:
                    f.write(l + "\n")
                    
        print(f"✅ Чистая сортировка для Н завершена! Прокси Трона защищены от дублирования.")

if __name__ == "__main__":
    sorter = CountrySorter()
    sorter.process_raw_data("v2ray_config_collector/data/raw/raw_configs.txt")
