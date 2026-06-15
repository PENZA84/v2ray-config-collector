"""
split_configs.py
Монолитный скрипт для разбиения очищенной базы на 5 ровных частей.
"""
import os
import glob
import math

def split_all_unique_configs(unique_dir="data/unique", num_chunks=5):
    os.makedirs(unique_dir, exist_ok=True)
    all_lines = []
    
    # 1. Собираем всё сырьё из папки уникальных данных
    for filepath in glob.glob(os.path.join(unique_dir, "*.txt")):
        filename = os.path.basename(filepath)
        if filename.startswith("chunk_") or filename.startswith("deduplicated"):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            all_lines.extend(lines)
        
        # Удаляем оригиналы, чтобы они не попали в артефакты и не путались
        try:
            os.remove(filepath)
        except:
            pass
            
    # Дополнительная защита: оставляем только уникальные
    all_lines = list(set(all_lines))
    total_lines = len(all_lines)
    print(f"📊 Всего чистых строк собрано для Валидатора: {total_lines}")
    
    if total_lines == 0:
        print("⚠️ Нет данных для разбивки.")
        return

    # 2. Режем строго на заданное количество кусков (5)
    chunk_size = math.ceil(total_lines / num_chunks)
    
    for i in range(num_chunks):
        chunk_lines = all_lines[i*chunk_size : (i+1)*chunk_size]
        chunk_name = f"chunk_{i+1:03d}.txt"
        
        with open(os.path.join(unique_dir, chunk_name), 'w', encoding='utf-8') as f:
            f.write("\n".join(chunk_lines) + "\n")
        
        print(f"✅ Создан кусок {chunk_name}: {len(chunk_lines)} строк")

if __name__ == "__main__":
    split_all_unique_configs("data/unique", num_chunks=5)
