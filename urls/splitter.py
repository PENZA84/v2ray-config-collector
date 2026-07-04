import asyncio
import aiohttp
import os
import argparse
import re

print("=== sorter.py запущен ===")

BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3', '.js', '.css']
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
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"

            text = await resp.text()
            text_lower = text.lower()
            url_lower = url.lower()
           
            if 't.me/proxy' in url_lower or 'mtproto' in url_lower:
                return "dead"

            if ('t.me/' in url_lower or '.m3u' in url_lower or '.m3u8' in url_lower or '#extm3u' in text_lower):
                return "misc"

            if any(x in url_lower for x in ['/https.txt', '/proxies', '/free-proxy', '/proxy-list', '/clash', '/v2ray', '/xray', 'freeclashnode', 'clashnodes', 'uploads/', '.txt']):
                return "factory"

            if re.search(r'[A-Za-z0-9+/=]{60,}', text):
                return "factory"

            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']):
                return "factory"

            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                return "factory"
           
            http_count = sum(1 for line in text.splitlines() if line.strip().startswith(('http://', 'https://')))
            if http_count >= 2:
                return "url_check"
           
            return "filtered"
    except Exception:
        return "dead"

async def process_window(window_id: int):
    chunks_dir = 'urls/urls'
    
    # 🔥 ПРЯМОЙ МАППИНГ: Окно X ищет строго файл chunk_X.txt
    target_file = f"chunk_{window_id}.txt"
    full_path = os.path.join(chunks_dir, target_file)

    if not os.path.exists(full_path):
        print(f"❌ Окно {window_id}: Целевой файл {target_file} не найден в {chunks_dir}!")
        return

    print(f"🚀 [Окно {window_id}] Начинаю обработку файла: {target_file}")

    factory, url_checks, filtered, dead, misc = [], [], [], [], []

    with open(full_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            url_lower = url.lower()
            if any(ext in url_lower for ext in BAD_EXT) or any(kw in url_lower for kw in BAD_KW):
                dead.append(url)
                continue

            category = await deep_check(session, url)
            if category == "factory":
                factory.append(url)
            elif category == "url_check":
                url_checks.append(url)
            elif category == "misc":
                misc.append(url)
            elif category == "dead":
                dead.append(url)
            else:
                filtered.append(url)

    # 📁 Сохраняем результаты во временные файлы с суффиксом окна
    for base_path, data in [
        ('urls/factory_valid', factory),
        ('urls/url_checks', url_checks),
        ('urls/misc', misc),
        ('urls/filtered_results', filtered)
    ]:
        if data:
            filename = f"{base_path}_{window_id}.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(data) + '\n')
            print(f"💾 Временное сохранение: {filename} ({len(data)} строк)")

    print(f"✅ [Окно {window_id}] Успешно завершено.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=0)
    args = parser.parse_args()

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(process_window(args.window))
