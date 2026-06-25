import asyncio
import aiohttp
import os
import re

BATCH_SIZE = 20000

# === СТРОГИЕ ФИЛЬТРЫ ===
BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']
BAD_KW = ['apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music', 
          'book', 'quote', 'steam', 'readme', 'youtube', 'boosty', 't.me/proxy', 'mtproto', 
          'blog.', 'medium.com', 'substack', 'telegra.ph', 'happ.su', 'bintv.net', 'applnn.com', 
          'tvlnn.com', 'techcrunch.com']

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"

            text = await resp.text()
            text_lower = text.lower()

            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']):
                return "factory"

            return "filtered"
    except:
        return "dead"

async def process_chunk(session, chunk_path):
    with open(chunk_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]
    
    print(f"   Обработка {os.path.basename(chunk_path)} ({len(urls)} ссылок)...")
    
    factory = []
    url_checks = []
    filtered = []
    dead = []

    for url in urls:
        url_lower = url.lower()
        if any(ext in url_lower for ext in BAD_EXT) or any(kw in url_lower for kw in BAD_KW):
            dead.append(url)
            continue

        category = await deep_check(session, url)

        if category == "factory":
            factory.append(url)
        elif category == "dead":
            dead.append(url)
        else:
            url_checks.append(url)

    return factory, url_checks, filtered, dead

async def main():
    chunks_dir = 'urls/urls'
    factory_file = 'urls/factory_valid.txt'
    url_checks_file = 'urls/url_checks.txt'
    filtered_file = 'urls/filtered_results.txt'
    dead_file = 'data/raw_incoming/deep_raw_collected.txt'

    if not os.path.exists(chunks_dir):
        print("❌ Папка urls/urls/ не найдена")
        return

    chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.startswith('chunk_') and f.endswith('.txt')])

    if not chunk_files:
        print("❌ Чанки не найдены в urls/urls/")
        return

    print(f"🔍 Найдено {len(chunk_files)} чанков. Начинаю обработку...\n")

    all_factory = []
    all_url_checks = []
    all_dead = []

    async with aiohttp.ClientSession() as session:
        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunks_dir, chunk_file)
            factory, url_checks, filtered, dead = await process_chunk(session, chunk_path)
            
            all_factory.extend(factory)
            all_url_checks.extend(url_checks)
            all_dead.extend(dead)

    # Склейка результатов
    with open(factory_file, 'a', encoding='utf-8') as f:
        if all_factory:
            f.write('\n'.join(all_factory) + '\n')

    with open(url_checks_file, 'a', encoding='utf-8') as f:
        if all_url_checks:
            f.write('\n'.join(all_url_checks) + '\n')

    with open(dead_file, 'a', encoding='utf-8') as f:
        if all_dead:
            f.write("\n# === Новый мусор + dead ===\n")
            f.write("\n".join(all_dead) + "\n")

    print("\n✅ Обработка всех чанков завершена!")
    print(f"   🏭 Factory: {len(all_factory)}")
    print(f"   🔗 Url_checks: {len(all_url_checks)}")
    print(f"   💀 В бункер: {len(all_dead)}")

    # Опционально: очистка чанков после обработки
    # for f in chunk_files:
    #     os.remove(os.path.join(chunks_dir, f))
    # print("🧹 Чанки удалены")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
