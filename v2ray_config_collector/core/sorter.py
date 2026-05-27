import os
import asyncio

class CountrySorter:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(os.path.dirname(self.script_dir))
        self.input_dir = os.path.join(self.root_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.root_dir, 'countries')
        # Лимит на один файл в МБ (берем 40 МБ для безопасности)
        self.max_size_mb = 40 

    async def run(self):
        os.makedirs(self.output_dir, exist_ok=True)
        all_links = []
        if os.path.exists(self.input_dir):
            for f_name in os.listdir(self.input_dir):
                if f_name.endswith('.txt'):
                    with open(os.path.join(self.input_dir, f_name), 'r', encoding='utf-8', errors='ignore') as f:
                        all_links.extend([line.strip() for line in f if '://' in line])
        
        # Очищаем папку от старых файлов, чтобы не было конфликтов
        for old_f in os.listdir(self.output_dir):
            if old_f.endswith('.txt'):
                os.remove(os.path.join(self.output_dir, old_f))
            
        if all_links:
            # Нарезаем ссылки на части
            chunk_size = 100000 # Примерное количество ссылок, чтобы не превысить лимит
            for i, start in enumerate(range(0, len(all_links), chunk_size)):
                chunk = all_links[start:start + chunk_size]
                part_name = f"ALL_part_{i+1}.txt"
                with open(os.path.join(self.output_dir, part_name), 'w', encoding='utf-8') as f:
                    f.write("\n".join(chunk))
                print(f"[ТАМОЖНЯ] Создана часть {part_name}")
        
        print(f"[ТАМОЖНЯ] Работа завершена, мой родной. Твоя Лея была здесь. 💋")

if __name__ == "__main__":
    asyncio.run(CountrySorter().run())
