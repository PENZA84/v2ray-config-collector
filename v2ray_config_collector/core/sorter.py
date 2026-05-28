import os
import asyncio
import re
from collections import defaultdict

# Это наш монолит: всё, что нужно для работы, внутри одного файла
# Чтобы избежать ошибок импорта, мы перенесли нужную логику прямо сюда

def extract_cc(uri):
    """Вытаскивает код страны из тега #CC_ или по IP"""
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

    async def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        grouped = defaultdict(list)
        
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            line = line.strip()
                            if '://' in line:
                                cc = extract_cc(line)
                                grouped[cc].append(line)
        
        # Записываем отсортированные данные
        for cc, links in grouped.items():
            path = os.path.join(self.output_dir, f"{cc}.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write("\n".join(links))
        
        print(f"[ЗАВОД] Сортировка завершена! Разложили по странам: {list(grouped.keys())}")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
