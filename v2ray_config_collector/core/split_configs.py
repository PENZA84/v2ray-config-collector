"""
split_configs.py
Монолитный скрипт для разбиения большого файла с прокси на части.
Выполняется ДО запуска валидатора.
"""

import os
from pathlib import Path

def split_file_into_chunks(input_path, output_dir, chunk_size=350_000):
    """
    Разбивает один большой файл на несколько кусков.
    Сохраняет в целевую папку с префиксом chunk_001.txt, chunk_002.txt и т.д.
    """
    input_file = Path(input_path)
    output_directory = Path(output_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_file}")

    # Очищаем старые чанки от прошлых запусков, чтобы не захламлять базу
    for old_chunk in output_directory.glob("chunk_*.txt"):
        old_chunk.unlink()
        print(f"🧹 Удаляю старый чанк из прошлого запуска: {old_chunk.name}")

    print(f"\n📂 Начинаю разбиение файла: {input_file.name}")
    print(f"📈 Размер одного чанка: {chunk_size} строк")

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"📊 Всего строк в файле для валидации: {total_lines}")

    # Создаём новые чанки
    created_chunks = 0
    for i in range(0, total_lines, chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_number = i // chunk_size + 1
        output_filename = f"chunk_{chunk_number:03d}.txt"
        output_path = output_directory / output_filename

        with open(output_path, 'w', encoding='utf-8') as out_f:
            out_f.writelines(chunk_lines)
        
        created_chunks += 1
        print(f"✅ Создан чанк {output_filename} (строки {i+1}-{min(i+chunk_size, total_lines)})")

    print(f"\n🎉 Разбиение завершено. Всего готово {created_chunks} частей для валидатора!")
    if created_chunks > 5:
        print(f"⚠️ Внимание! У нас получилось {created_chunks} чанков, не забудь добавить недостающие шаги запуска в main.yml")


if __name__ == "__main__":
    # ПУТИ К ФАЙЛАМ (ПОДОГНАНЫ ПОД СТРУКТУРУ НАШЕГО ЗАВОДА)
    # Большой очищенный файл со всеми уникальными прокси от main.py
    INPUT_FILE = "data/unique/all_configs.txt"
    # Папка куда сохраняем чанки — строго туда, где их ждет валидатор из main.yml
    OUTPUT_CHUNKS_FOLDER = "data/unique/"
    
    split_file_into_chunks(INPUT_FILE, OUTPUT_CHUNKS_FOLDER)
