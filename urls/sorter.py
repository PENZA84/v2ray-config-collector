import asyncio
import aiohttp
import os
import argparse

BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']

BAD_KW = [
    'apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music',
    'book', 'quote', 'steam', 'readme', 'youtube', 'boosty', 't.me/proxy', 'mtproto',
    'blog.', 'medium.com', 'substack', 'telegra.ph', 'happ.su', 'bintv.net', 'applnn.com',
    'tvlnn.com', 'techcrunch.com', 'gugu3.com/', 'donate', 'instagram', 'wikipedia',
    'videosearch', 'artist', 'tv', 'tv.', 'article', 'google.com', 'translate.google',
    'translate', 'microsoft.com', 'bing.com', 'outlook.com', 'github.com', 'gitlab.com',
    'bitbucket.org', 'wikipedia.org', 'wiki', 'msn.com', 'news'
]

async def deep_check(session, url: str):
    try:
        print(f"   🔍 Проверяем: {url}")
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
            if resp.status != 200:
                print(f"   ❌ Dead (status {resp.status}): {url}")
                return "dead"
            text = await resp.text()
            text_lower = text.lower()
            
            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']):
                print(f"   ✅ Factory (протокол): {url}")
                return "factory"
            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                print(f"   ✅ Factory (subscription): {url}")
                return "factory"
            
            http_count = sum(1 for line in text.splitlines() if line.strip().startswith(('http://', 'https://')))
            if http_count >= 5:
                print(f"   🔗 Url_check (много ссылок): {url}")
                return "url_check"
            print(f"   🗑 Filtered: {url}")
            return "filtered"
    except Exception as e:
        print(f"   ❌ Dead (ошибка): {url} | {e}")
        return "dead"

async def process_window(window_id: int):
    chunks_dir = 'urls/urls'
    if not os.path.exists(chunks_dir):
        print(f"❌ Окно {window_id}: Папка чанков не найдена!")
        return

    chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.startswith('chunk_')])
    my_chunks = [f for i, f in enumerate(chunk_files) if i % 10 == window_id]

    print(f"🚀 [Окно {window_id}] Найдено чанков: {len(my_chunks)} → {my_chunks}")

    factory, url_checks, filtered, dead = [], [], [], []

    async with aiohttp.ClientSession() as session:
        for chunk_file in my_chunks:
            full_path = os.path.join(chunks_dir, chunk_file)
            with open(full_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]

            print(f"   📂 Обрабатываем чанк: {chunk_file} ({len(urls)} ссылок)")

            for url in urls:
                url_lower = url.lower()
                if any(ext in url_lower for ext in BAD_EXT) or any(kw in url_lower for kw in BAD_KW):
                    print(f"   🗑 BAD_KW/BAD_EXT: {url}")
                    dead.append(url)
                    continue

                category = await deep_check(session, url)
                if category == "factory":
                    factory.append(url)
                elif category == "url_check":
                    url_checks.append(url)
                elif category == "dead":
                    dead.append(url)
                else:
                    filtered.append(url)

    # Сохранение
    for filename, data in [
        ('urls/factory_valid.txt', factory),
        ('urls/url_checks.txt', url_checks),
        ('urls/filtered_results.txt', filtered)
    ]:
        if data:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'a', encoding='utf-8') as f:
                f.write('\n'.join(data) + '\n')

    if dead:
        dead_file = 'data/raw_incoming/deep_raw_collected.txt'
        os.makedirs(os.path.dirname(dead_file), exist_ok=True)
        with open(dead_file, 'a', encoding='utf-8') as f:
            f.write(f"\n# === Dead from window {window_id} ===\n")
            f.write('\n'.join(dead) + '\n')

    print(f"✅ [Окно {window_id}] Завершено → Factory: {len(factory)}, Url_checks: {len(url_checks)}, Filtered: {len(filtered)}, Dead: {len(dead)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=0)
    args = parser.parse_args()

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(process_window(args.window))
