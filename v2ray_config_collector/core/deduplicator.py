import os
from datetime import datetime
from collections import defaultdict

class ConfigDeduplicator:
    def __init__(self, input_file=None, output_dir=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Теперь берем из уникальных после парсера, но перед валидатором
        self.input_file = input_file or os.path.join(package_dir, 'data', 'unique', 'deduplicated.txt')
        self.output_dir = output_dir or os.path.join(package_dir, 'data', 'unique')
        
        self.stats = {
            'total_configs': 0,
            'unique_configs': 0,
            'duplicates_removed': 0,
            'protocols': defaultdict(int)
        }

    def process(self):
        if not os.path.exists(self.input_file):
            print(f"⚠️ Файл не найден: {self.input_file}")
            return False

        print("🚀 Запуск текстовой дедупликации...")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            # Читаем все строки, убираем пустые
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        self.stats['total_configs'] = len(lines)
        
        # Основная магия дедупликации через set
        unique_lines = list(set(lines))
        self.stats['unique_configs'] = len(unique_lines)
        self.stats['duplicates_removed'] = self.stats['total_configs'] - self.stats['unique_configs']

        # Разделение по протоколам для статистики
        protocol_groups = defaultdict(list)
        for line in unique_lines:
            proto = line.split('://')[0] if '://' in line else 'unknown'
            self.stats['protocols'][proto] += 1
            protocol_groups[proto].append(line)

        # Сохраняем основной файл (перезаписываем deduplicated.txt чистым списком)
        os.makedirs(self.output_dir, exist_ok=True)
        with open(os.path.join(self.output_dir, 'deduplicated.txt'), 'w', encoding='utf-8') as f:
            f.write("\n".join(unique_lines))

        # Сохраняем по протоколам (как ты любишь)
        protocols_dir = os.path.join(self.output_dir, 'protocols')
        os.makedirs(protocols_dir, exist_ok=True)
        
        for proto, configs in protocol_groups.items():
            proto_file = os.path.join(protocols_dir, f'{proto}_configs.txt')
            with open(proto_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(configs))

        self.print_summary()
        return True

    def print_summary(self):
        print(f"\nИТОГИ ДЕДУПЛИКАЦИИ:")
        print(f"================================")
        print(f"Всего обработано: {self.stats['total_configs']}")
        print(f"Уникальных:       {self.stats['unique_configs']}")
        print(f"Удалено дублей:   {self.stats['duplicates_removed']}")
        print(f"Снижение объема:  {(self.stats['duplicates_removed']/self.stats['total_configs']*100):.1f}%" if self.stats['total_configs'] > 0 else "0%")
        print(f"\nПо протоколам:")
        for proto, count in self.stats['protocols'].items():
            print(f"  - {proto}: {count}")
        print(f"================================\n")

if __name__ == "__main__":
    deduplicator = ConfigDeduplicator()
    deduplicator.process()
