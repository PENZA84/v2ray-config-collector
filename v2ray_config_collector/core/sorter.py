import os
import asyncio
import re
from collections import defaultdict

def extract_cc(uri):
    """Вытаскивает код страны из тега #CC_ или по знакам в ссылке"""
    match = re.search(r'#([A-Z]{2})_', uri)
    if match:
        return match.group(1).upper()
    return 'UNKNOWN'

class CountrySorter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        # Лимит строк в одном файле, чтобы размер гарантированно не превышал ~50-85 МБ
        self.max_lines_per_file = 200000 

    async def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        grouped = defaultdict(list)
        
        # Читаем входные данные
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if '://' in line:
                                cc = extract_cc(line)
                                grouped[cc].append(line)
        
        # Записываем отсортированные данные с защитой от превышения размера
        for cc, links in grouped.items():
            total_links = len(links)
            
            if total_links <= self.max_lines_per_file:
                # Если файл небольшой, пишем как обычно
                path = os.path.join(self.output_dir, f"{cc}.txt")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(links))
            else:
                # Если ссылок слишком много (как в UNKNOWN), бьем их на части
                print(f"[ЗАВОД] Файл {cc}.txt слишком большой ({total_links} строк). Разделяем на части...")
                part_num = 1
                for i in range(0, total_links, self.max_lines_per_file):
                    chunk = links[i:i + self.max_lines_per_file]
                    path = os.path.join(self.output_dir, f"{cc}_{part_num}.txt")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(chunk))
                    part_num += 1
        
        print(f"[ЗАВОД] Сортировка завершена! Все файлы адаптированы под лимиты GitHub.")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
