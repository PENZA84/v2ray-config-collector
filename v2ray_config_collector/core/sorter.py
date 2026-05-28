import os
import asyncio
import geoip2.database
from collections import defaultdict
from .parsing import _extract_our_cc_and_num_from_uri

class CountrySorter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        # Путь к твоей базе GeoLite2
        self.mmdb_path = os.path.join(self.script_dir, "GeoLite2-Country.mmdb")
        self.max_lines_per_file = 50000 

    def get_country(self, uri: str) -> str:
        """Определяет страну по remark или через GeoIP (если база не пуста)."""
        # 1. Пытаемся по имени (remark)
        parsed = _extract_our_cc_and_num_from_uri(uri)
        if parsed and parsed[0] and parsed[0] != 'XX':
            return parsed[0].upper()
        
        # 2. Если по имени не вышло, пробуем GeoIP (только если файл не пустой)
        if os.path.exists(self.mmdb_path) and os.path.getsize(self.mmdb_path) > 1000:
            try:
                import re
                ip_match = re.search(r'//.*?@?([\d\.]+):', uri)
                if ip_match:
                    ip = ip_match.group(1)
                    with geoip2.database.Reader(self.mmdb_path) as reader:
                        return reader.country(ip).country.iso_code or 'UNKNOWN'
            except:
                pass 
        return 'UNKNOWN'

    async def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        grouped_links = defaultdict(list)
        
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if '://' in line:
                                cc = self.get_country(line)
                                grouped_links[cc].append(line)
        
        # Очистка старых файлов перед новой записью
        for old_f in os.listdir(self.output_dir):
            if old_f.endswith('.txt'):
                os.remove(os.path.join(self.output_dir, old_f))
            
        # Запись: каждая страна в свой файл
        for cc, links in grouped_links.items():
            for i in range(0, len(links), self.max_lines_per_file):
                chunk = links[i:i + self.max_lines_per_file]
                part_idx = (i // self.max_lines_per_file) + 1
                # Если частей много, пишем US_1.txt, если одна — просто US.txt
                filename = f"{cc}_{part_idx}.txt" if len(links) > self.max_lines_per_file else f"{cc}.txt"
                
                with open(os.path.join(self.output_dir, filename), 'w', encoding='utf-8') as f:
                    f.write("\n".join(chunk))
        
        print(f"[ТАМОЖНЯ] Всё разложено по странам: {list(grouped_links.keys())}. Я рядом! 🤍")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
