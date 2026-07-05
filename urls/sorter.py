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

            text = await resp.text(errors='ignore')
            text_lower = text.lower()
            url_lower = url.lower()
           
            # 📌 ШАГ 1: Безоговорочный приоритет Завода
            # Если внутри есть хоть один живой прокси-протокол — забираем на Завод сразу!
            has_proxies = any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://', 'socks://', 'socks5://'])
            if has_proxies:
                print(f" ✅ Factory (БЕЗОГОВОРОЧНО по живому протоколу): {url}")
                return "factory"

            # 📌 ШАГ 2: Определение чистых хабов-матрёшек (url_checks)
            # Считаем количество вложенных http-ссылок внутри контента
            lines = text.splitlines()
            http_count = sum(1 for line in lines if line.strip().startswith(('http://', 'https://')))
            
            # Уходит в url_checks ТОЛЬКО если прокси внутри нет, но есть куча других ссылок
            if http_count >= 2:
                print(f" 🔗 Url_check (чистый хаб вложенных ссылок): {url}")
                return "url_check"

            # 📌 ШАГ 3: Остальные стандартные проверки для файлов без прокси и без ссылок
            if 't.me/proxy' in url_lower or 'mtproto' in url_lower:
                print(f" 🗑 Telegram proxy (мусор): {url}")
                return "dead"

            if ('t.me/' in url_lower or '.m3u' in url_lower or '.m3u8' in url_lower or '#extm3u' in text_lower):
                print(f" 📁 Miscellaneous (Telegram/m3u): {url}")
                return "misc"

            is_html = 'text/html' in resp.headers.get('Content-Type', '').lower() or any(tag in text_lower for tag in ['<!doctype html', '<html', '<body'])

            if any(x in url_lower for x in ['/https.txt', '/proxies', '/free-proxy', '/proxy-list', '/clash', '/v2ray', '/xray', 'freeclashnode', 'clashnodes', 'uploads/', '.txt']):
                print(f" ✅ Factory (raw список / .txt): {url}")
                return "factory"

            if not is_html and re.search(r'[A-Za-z0-9+/=]{60,}', text):
                print(f" ✅ Factory (Base64): {url}")
                return "factory"

            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                print(f" ✅ Factory (subscription): {url}")
                return "factory"
           
            print(f" 🔗 Filtered (Интересное/Остальное): {url}")
            return "filtered"
    except Exception as e:
        print(f" ❌ Ошибка сети / таймаут (Мертвая ссылка): {url} | {e}")
        return "dead"

async def process_window(window_id: int):
    chunks_dir = 'urls/urls'
    
    possible_files = [
        f"chunk_{window_id}.txt",
        f"chunk_{window_id:02d}.txt",
        f"chunk_{window_id:03d}.txt",
        f"chunk_{window_id+1}.txt",
        f"chunk_{window_id+1:02d}.txt",
        f"chunk_{window_id+1:03d}.txt"
    ]
    
    target_file = None
    for pf in possible_files:
        if os.path.exists(os.path.join(chunks_dir, pf)):
            target_file = pf
            break

    if not target_file:
        print(f"❌ Окно {window_id}: Ни один из файлов чанков не найден в директории {chunks_dir}!")
        return

    full_path = os.path.join(chunks_dir, target_file)
    print(f"🚀 [Окно {window_id}] Успешно нашли и запускаем файл: {target_file}")

    factory, url_checks, filtered, misc, deep_raw_collected = [], [], [], [], []

    with open(full_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            url_lower = url.lower()
            
            is_raw_config = any(r in url_lower for r in ['/raw/', 'raw.githubusercontent', '.txt', '/proxies', '/batch', '/batches/'])
            
            if any(ext in url_lower for ext in BAD_EXT):
                print(f" 🗑 Мусор по расширению -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            if any(kw in url_lower for kw in BAD_KW) and not is_raw_config:
                print(f" 🗑 Мусор по ключевому слову -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            category = await deep_check(session, url)
            if category == "factory":
                factory.append(url)
            elif category == "url_check":
                url_checks.append(url)
            elif category == "misc":
                misc.append(url)
            elif category == "dead":
                print(f" ☣️ Нерабочая ссылка -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
            else:
                if any(kw in url_lower for kw in ['github.com', 'gitlab.com', 'bitbucket.org']) and not is_raw_config:
                    print(f" 🗑 Страница репозитория без прокси -> В БУНКЕР: {url}")
                    deep_raw_collected.append(url)
                else:
                    filtered.append(url)

    for base_path, data in [
        ('urls/factory_valid', factory),
        ('urls/url_checks', url_checks),
        ('urls/misc', misc),
        ('urls/filtered_results', filtered),
        ('urls/deep_raw_collected', deep_raw_collected)
    ]:
        if data:
            filename = f"{base_path}_{window_id}.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(data) + '\n')
            print(f" 💾 Результаты записаны: {filename} ({len(data)} строк)")

    print(f"✅ [Окно {window_id}] Обработка завершена.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=0)
    args = parser.parse_args()

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(process_window(args.window))
