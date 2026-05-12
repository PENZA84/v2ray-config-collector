import os

class ConfigDeduplicator:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def deduplicate(self):
        if not os.path.exists(self.input_file):
            return
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        unique_lines = list(set([line.strip() for line in lines if line.strip()]))
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(unique_lines))
        
        print(f"✨ Удалено дублей. Осталось уникальных: {len(unique_lines)}")
