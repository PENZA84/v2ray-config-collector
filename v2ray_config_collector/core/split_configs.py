"""
split_configs.py
Монолитный скрипт для разбиения большого файла с прокси на части.
Выполняется ДО запуска валидатора.
"""

import os
from pathlib import Path

def split_file_into_chunks(input_path, chunk_size=1_000_000):
    """
    Разбивает один большой файл на несколько кусков.
    Сохраняет в ту же папку с префиксом chunk_001.txt, chunk_002.txt и т.д.
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_path}")

    print(f"📂 Начинаю разбиение файла: {input_file.name}")
    print(f"📈 Размер чанка: {chunk_size} строк")

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"📊 Всего строк в файле: {total_lines}")

    # Создаём чанки
    for i in range(0, total_lines, chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_number = i // chunk_size + 1
        output_filename = f"chunk_{chunk_number:03d}.txt"
        output_path = input_file.parent / output_filename

        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.writelines(chunk_lines)

        print(f"✅ Создан чанк {output_filename} (строки {i+1}-{min(i+chunk_size, total_lines)})")

    print(f"\n🎉 Разбиение завершено. Создано {len(list(input_file.parent.glob('chunk_*.txt')))} частей.")


if __name__ == "__main__":
    # ПУТЬ К ВАШЕМУ ФАЙЛУ (НЕ МЕНЯТЬ, ЕСЛИ СТРУКТУРА ПАПКИ СТАНДАРТНАЯ)
    INPUT_FILE = "data/unique/extracted_documents.txt"
    
    split_file_into_chunks(INPUT_FILE)
