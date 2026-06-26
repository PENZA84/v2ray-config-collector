import os

BATCH_SIZE = 20000  # по 20 тысяч на чанк

def main():
    input_file = 'urls/source_urls.txt'
    chunks_dir = 'urls/urls'
    os.makedirs(chunks_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print("❌ source_urls.txt не найден")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

    print(f"🔍 Всего ссылок: {len(urls)}")
    print(f"📦 Разбиваю на чанки по {BATCH_SIZE} ссылок...\n")

    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        chunk_file = f"{chunks_dir}/chunk_{batch_num:03d}.txt"
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(batch) + '\n')
        
        print(f"✅ Сохранён {chunk_file} ({len(batch)} ссылок)")

    # Очищаем основной файл
    open(input_file, 'w').close()
    print("\n🧹 source_urls.txt очищен")
    print(f"🎉 Разбито на {((len(urls)-1)//BATCH_SIZE)+1} чанков")

if __name__ == "__main__":
    main()
