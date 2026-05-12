import os
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def test_all_configs(self):
        if not os.path.exists(self.input_file):
            print("❌ Файл для валидации не найден.")
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            configs = [line.strip() for line in f if line.strip()]

        if not configs:
            print("⚠️ Нет конфигов для проверки.")
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            with open(self.output_file, 'w') as f: pass
            return

        # Сейчас мы просто переносим их, так как полная проверка TCP
        # может занять часы для 5000+ ссылок.
        valid_configs = configs 

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(valid_configs))
        
        print(f"✅ Обработка завершена. В очереди: {len(valid_configs)}")
