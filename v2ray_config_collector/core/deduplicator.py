import json
import os
import hashlib
import sys
import base64
import urllib.parse
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm
import time

class ConfigDeduplicator:
    def __init__(self, input_file=None, output_dir=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_file = input_file or os.path.join(package_dir, 'data', 'processed', 'normalized_configs.json')
        self.output_dir = output_dir or os.path.join(package_dir, 'data', 'unique')
        self.stats = {'total_configs': 0, 'unique_configs': 0, 'duplicates_removed': 0, 'protocols': defaultdict(int)}
        self.configs = []
        self.unique_configs = []
        self.existing_hashes = set()

    def load_configs(self):
        """Загружает базу с защитой от повреждений"""
        existing_json_path = os.path.join(self.output_dir, 'deduplicated.json')
        if os.path.exists(existing_json_path):
            try:
                with open(existing_json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_list = existing_data.get('configs', []) if isinstance(existing_data, dict) else []
                    for ext_conf in existing_list:
                        self.unique_configs.append(ext_conf)
                        self.existing_hashes.add(self.generate_config_hash(ext_conf))
                print(f"✅ База загружена: {len(self.unique_configs)} элементов.")
            except Exception as e:
                print(f"⚠️ Ошибка чтения базы, начинаем с чистого листа: {e}")

        if not os.path.exists(self.input_file): return len(self.unique_configs) > 0
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.configs = data.get('configs', data) if isinstance(data, (dict, list)) else []
        return True

    def generate_config_hash(self, config):
        """Строгий хэш для контроля уникальности"""
        protocol = config.get('type', 'unknown')
        key_parts = [f"type:{protocol}"]
        for field in ['server', 'port', 'uuid', 'password', 'remarks', 'path', 'sni']:
            if config.get(field): key_parts.append(f"{field}:{str(config[field]).strip()}")
        return hashlib.md5('|'.join(key_parts).encode('utf-8')).hexdigest()

    def find_duplicates(self):
        """Поиск дублей с учетом существующих hash-слепков"""
        hash_to_configs = defaultdict(list)
        for config in self.configs:
            h = self.generate_config_hash(config)
            if h not in self.existing_hashes:
                hash_to_configs[h].append(config)
        
        for h, group in hash_to_configs.items():
            best = max(group, key=lambda x: sum(1 for v in x.values() if v))
            self.unique_configs.append(best)
            self.existing_hashes.add(h)

    def save_all_configs(self):
        """Атомарная запись для предотвращения порчи базы"""
        output_data = {
            'metadata': {'generated_at': datetime.now().isoformat()},
            'configs': [self.clean_config(c) for c in self.unique_configs]
        }
        
        tmp_file = os.path.join(self.output_dir, 'deduplicated.json.tmp')
        final_file = os.path.join(self.output_dir, 'deduplicated.json')
        
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, final_file) # Атомарная замена
        print("💾 База защищена и сохранена.")

    def clean_config(self, config):
        """Очистка от служебных меток без изменения оригинала"""
        return {k: v for k, v in config.items() if not k.startswith('_')}

    # Методы reconstruct_... остаются без изменений, они у тебя написаны отлично
    def reconstruct_vmess_url(self, config):
        # ... (твой код)
        pass 

    def process(self):
        if self.load_configs():
            self.find_duplicates()
            self.save_all_configs()
            return True
        return False

if __name__ == "__main__":
    ConfigDeduplicator().process()
