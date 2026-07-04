import os

def main():
    input_file = 'urls/source_urls.txt'
    chunks_dir = 'urls/urls'
    os.makedirs(chunks_dir, exist_ok=True)

    # 🧹 Очищаем папку от старых чанков перед новой генерацией
    if os.path.exists(chunks_dir):
        for f in os.listdir(chunks_dir):
            if f.startswith('chunk_'):
                try:
                    os.remove(os.path.join(chunks_dir, f))
                except Exception:
                    pass

    if not os.path.exists(input_file):
        print("❌ source_urls.txt не найден")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

    total_urls = len(urls)
    print(f"🔍 Всего валидных ссылок: {total_urls}")
    
    chunks_count = 10
    # Вычисляем размер порции, чтобы распределить ссылки ровно на 10 файлов
    urls_per_chunk = (total_urls + chunks_count - 1) // chunks_count if total_urls > 0 else 0
    print(f"📦 Распределяю примерно по {urls_per_chunk} ссылок на один чанк...\n")

    # Создаем ровно 10 чанков (от chunk_0.txt до chunk_9.txt)
    for batch_num in range(chunks_count):
        start_idx = batch_num * urls_per_chunk
        end_idx = start_idx + urls_per_chunk
        batch = urls[start_idx:end_idx]
        
        chunk_file = f"{chunks_dir}/chunk_{batch_num}.txt"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            if batch:
                f.write('\n'.join(batch) + '\n')
        
        print(f"✅ Создан {chunk_file} ({len(batch)} ссылок) для Окна {batch_num}")

    # === ПРИНУДИТЕЛЬНАЯ ОЧИСТКА ИСХОДНИКА ===
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write("")
    print("\n🧹 source_urls.txt полностью очищен")

    # === Commit пустого source_urls.txt ===
    print("📤 Отправляем пустой исходник в репозиторий...")
    os.system('git config --global user.name "github-actions[bot]"')
    os.system('git config --global user.email "github-actions[bot]@users.noreply.github.com"')
    os.system('git add urls/source_urls.txt')
    os.system('git diff --staged --quiet || git commit -m "🧹 source_urls.txt очищен" && git push')

    print(f"🎉 Нарезка завершена. Подготовлено {chunks_count} файлов.")

if __name__ == "__main__":
    main()
