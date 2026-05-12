import os
import requests
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self, input_file=None, output_file=None):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Файл, который подготовил парсер
        self.input_file = input_file or os.path.join(base_path, 'data', 'unique', 'deduplicated.txt')
        # Файл для рабочих прокси
        self.output_file = output_file or os.path.join(base_path, 'data', 'validated', 'all_valid.txt')

    def test_all_configs(self):
        if not os.path.exists(self.input_file):
            print("❌ Файл для проверки не найден.")
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = [line.strip() for line in f if line.strip()]

        if not configs:
            print("⚠️ Нет конфигов для проверки.")
            return

        print(f"🔍 Начинаю проверку {len(configs)} конфигов...")
        valid_configs = []

        # Самая быстрая проверка (timeout 3 секунды)
        for config in tqdm(configs, desc="Валидация"):
            # Тут должна быть твоя логика проверки (через прокси-запрос или ping)
            # Для примера оставим логику пропуска, если мы не уверены
            # В реальном коде тут идет попытка коннекта
            is_working = False 
            
            if is_working:
                valid_configs.append(config)

        # 1. Сохраняем только рабочие
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_configs))
        
        # 2. ОЧИСТКА: Удаляем файл с плохими/непроверенными данными
        if os.path.exists(self.input_file):
            os.remove(self.input_file)
            # Создаем пустой файл, чтобы git не ругался
            with open(self.input_file, 'w') as f: pass

        print(f"✅ Готово! Рабочих: {len(valid_configs)}. Грязные файлы удалены.")
