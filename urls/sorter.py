import os

def main():
    input_file = 'urls/source_urls.txt'
    chunks_dir = 'urls/urls'
    os.makedirs(chunks_dir, exist_ok=True)

    # 🧹 Полностью очищаем папку от старых чанков перед новой нарезкой
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
    print(f"🔍 Всего ссылок в source_urls.txt: {total_urls}")
    
    chunks_count = 10
    urls_per_chunk = (total_urls + chunks_count - 1) // chunks_count if total_urls > 0 else 0
    print(f"📦 Динамический размер чанка: ~{urls_per_chunk} строк.")

    # Создаем ровно 10 файлов: от chunk_0.txt до chunk_9.txt
    for batch_num in range(chunks_count):
        start_idx = batch_num * urls_per_chunk
        end_idx = start_idx + urls_per_chunk
        batch = urls[start_idx:end_idx]
        
        chunk_file = f"{chunks_dir}/chunk_{batch_num}.txt"
        with open(chunk_file, 'w', encoding='utf-8') as f:
            if batch:
                f.write('\n'.join(batch) + '\n')
        print(f"✅ Сохранён {chunk_file} ({len(batch)} ссылок) для Окна {batch_num}")

    # === ПРИНУДИТЕЛЬНАЯ ОЧИСТКА ИСХОДНИКА ===
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write("")
    print("\n🧹 source_urls.txt полностью очищен")

    # === Commit только очищенного файла ===
    print("📤 Коммитим пустой source_urls.txt...")
    os.system('git config --global user.name "github-actions[bot]"')
    os.system('git config --global user.email "github-actions[bot]@users.noreply.github.com"')
    os.system('git add urls/source_urls.txt')
    os.system('git diff --staged --quiet || git commit -m "🧹 source_urls.txt очищен" && git push')

    print(f"🎉 Все ссылки успешно распределены по 10 файлам (chunk_0 - chunk_9)")

if __name__ == "__main__":
    main()
