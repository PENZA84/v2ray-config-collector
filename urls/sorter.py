import asyncio
import aiohttp
import os
import argparse
import re

print("=== sorter.py [Абсолютный Монолит V3.1] запущен ===")

# =====================================================================
# 🔥 ГЛОБАЛЬНЫЕ БАЗЫ ФИЛЬТРАЦИИ (НАСТРОЙКА ЗАВОДА)
# =====================================================================

# 🛑 1. СТРОГО ЗАПРЕЩЕННЫЕ РАСШИРЕНИЯ (Блокируются всегда и везде)
BAD_EXT = [
    '.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', 
    '.mp4', '.mp3', '.js', '.css', '.sh', '.png', '.jpg', '.jpeg', 
    '.gif', '.dmg', '.7z'
]

# 🛑 2. БЕЗУСЛОВНЫЙ БАН (Уничтожаются мгновенно, даже если это raw/txt ссылки)
# Сюда улетают лицензии, корпоративный шум, медиа-порталы и мусорные сервисы
ALWAYS_BAD_KW = [
    'opera.com', 'ubuntu.com', 'ashampoo.com', 'twitter.com', 'x.com', 'rt.com', 
    'tf1.fr', 'testingcatalog.com', 'thegamer.com', 'tomsguide.com', 'safewise.com', 
    'techradar.com', 'startnext.com', 'pixiv.net', 'zap-mag.ru', 'zava.io', 'yoyapai.com',
    'amnezia.org/documentation', 'amnezia.org/ru/documentation', 'doc.qt.io', 
    'docs.ansible.com', 'docs.astral.sh', 'docs.aws.amazon.com', 'docs.breezometer.com',
    'docs.cherry-ai.com', 'docs.cloudbees.com', 'docs.coolercontrol.org', 'docs.gramaddict.org',
    'todo.txt', 'activefilerecovery', 
    'license',       # Намертво выжигает LICENSE.txt на GitHub до траты сетевых запросов
    'amazonaws.com'  # 🔥 ЗАЩИТА: Выкашивает мусорные S3-хранилища Амазона прямо в бункер
]

# 🛑 3. БАН СТРАНИЦ-ОБОЛОЧЕК (Если это сырой конфиг /raw/ или .txt — пропускаем внутрь!)
BAD_KW = [
    'apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music',
    'book', 'quote', 'steam', 'readme', 'boosty', 't.me/proxy', 'mtproto',
    'blog.', 'medium.com', 'substack', 'telegra.ph', 'happ.su', 'bintv.net', 'applnn.com',
    'tvlnn.com', 'techcrunch.com', 'gugu3.com/', 'donate', 'wikipedia',
    'videosearch', 'artist', 'tv', 'tv.', 'article', 'google.com', 'translate.google',
    'translate', 'microsoft.com', 'bing.com', 'outlook.com', 'github.com', 'gitlab.com',
    'bitbucket.org', 'wikipedia.org', 'wiki', 'msn.com', 'news'
]

# =====================================================================
# ⚙️ ИСПОЛНИТЕЛЬНОЕ ЯДРО
# =====================================================================

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"

            text = await resp.text(errors='ignore')
            text_lower = text.lower()
            url_lower = url.lower()

            # Шаг 1: Поиск живых прокси-протоколов
            has_proxies = any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://', 'socks://', 'socks5://'])
            if has_proxies:
                print(f" ✅ Factory (Живой протокол): {url}")
                return "factory"

            is_html = 'text/html' in resp.headers.get('Content-Type', '').lower() or any(tag in text_lower for tag in ['<!doctype html', '<html', '<body'])

            # Шаг 2: Проверка на сырые списки / txt конфигурации
            if any(x in url_lower for x in ['/https.txt', '/proxies', '/free-proxy', '/proxy-list', '/clash', '/v2ray', '/xray', 'freeclashnode', 'clashnodes', 'uploads/', '.txt']):
                print(f" ✅ Factory (Raw/Txt подписка): {url}")
                return "factory"

            # Поиск Base64 только в не-HTML страницах
            if not is_html and re.search(r'[A-Za-z0-9+/=]{60,}', text):
                print(f" ✅ Factory (Чистый Base64 маркер): {url}")
                return "factory"

            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                print(f" ✅ Factory (Subscription подпись): {url}")
                return "factory"

            # Шаг 3: Определение медиа-потоков
            if ('.m3u' in url_lower or '.m3u8' in url_lower or '#extm3u' in text_lower):
                print(f" 📁 Miscellaneous (m3u): {url}")
                return "misc"

            # Шаг 4: Поиск хабов ссылок
            if not is_html:
                lines = text.splitlines()
                http_count = sum(1 for line in lines if line.strip().startswith(('http://', 'https://')))
                if http_count >= 2:
                    print(f" 🔗 Url_check (Сырой хаб ссылок): {url}")
                    return "url_check"
            
            print(f" 🔗 Filtered (Остальной потенциальный интерес): {url}")
            return "filtered"
    except Exception as e:
        print(f" ❌ Ошибка сети (Мертвая ссылка): {url} | {e}")
        return "dead"

async def process_window(window_id: int):
    chunks_dir = 'urls/urls'
    
    possible_files = [
        f"chunk_{window_id}.txt", f"chunk_{window_id:02d}.txt", f"chunk_{window_id:03d}.txt",
        f"chunk_{window_id+1}.txt", f"chunk_{window_id+1:02d}.txt", f"chunk_{window_id+1:03d}.txt"
    ]
    
    target_file = None
    for pf in possible_files:
        if os.path.exists(os.path.join(chunks_dir, pf)):
            target_file = pf
            break

    if not target_file:
        print(f"❌ Файл чанка для окна {window_id} не найден!")
        return

    full_path = os.path.join(chunks_dir, target_file)
    print(f"🚀 Запуск обработки файла: {target_file}")

    factory, url_checks, filtered, misc, deep_raw_collected = [], [], [], [], []

    with open(full_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            url_lower = url.lower()
            
            # 🛑 ПЕРЕХВАТ 1: Telegram Веб-каналы уходят строго в misc
            if 't.me/' in url_lower:
                print(f" 📁 Telegram Ссылка -> Строго в misc: {url}")
                misc.append(url)
                continue

            # 🛑 ПЕРЕХВАТ 2: Криптовалютный мусор
            if any(c in url_lower for c in ['novadax.com', 'coinbase.com', 'cryptocurrency', 'cryptocurrencies', 'blockchain', 'coincap.io', 'bnbchain.org']):
                print(f" 🗑 Крипто-мусор -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            # 🛑 ПЕРЕХВАТ 3: Безусловный бан глобального мусора (Лицензии, личные доки, медиа, Амазон)
            if any(junk in url_lower for junk in ALWAYS_BAD_KW) or any(ext in url_lower for ext in BAD_EXT):
                print(f" 🗑 Тотальный мусор/документация -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            # Проверка флага сырых данных для ИИ и Оболочек
            is_raw_config = any(r in url_lower for r in ['/raw/', 'raw.githubusercontent', '.txt', '/proxies'])

            # 🛑 ПЕРЕХВАТ 4: Шлюз для ИИ-сервисов (если это не прямая ссылка на конфиг)
            AI_SERVICES = ['grok.com', 'rask.ai', 'openai.com', 'claude.ai', 'huggingface.co', 'gemini.com']
            if any(ai in url_lower for ai in AI_SERVICES) and not is_raw_config:
                print(f" 🤖 AI Сервис -> Строго в filtered_results: {url}")
                filtered.append(url)
                continue

            # 🛑 ПЕРЕХВАТ 5: Обычный черный список ключевых слов (с поблажкой для raw)
            if any(kw in url_lower for kw in BAD_KW) and not is_raw_config:
                print(f" 🗑 Мусорное ключевое слово -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            # Глубокий сетевой анализ выживших кандидатов
            category = await deep_check(session, url)
            if category == "factory":
                factory.append(url)
            elif category == "url_check":
                url_checks.append(url)
            elif category == "misc":
                misc.append(url)
            elif category == "dead":
                deep_raw_collected.append(url)
            else:
                if any(kw in url_lower for kw in ['github.com', 'gitlab.com', 'bitbucket.org']) and not is_raw_config:
                    print(f" 🗑 Репозиторий без raw-данных -> В БУНКЕР: {url}")
                    deep_raw_collected.append(url)
                else:
                    filtered.append(url)

    # Сохранение результатов
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
            print(f" 💾 Сохранено: {filename} ({len(data)} строк)")

    print(f"✅ [Окно {window_id}] Поток полностью обработан.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=0)
    args = parser.parse_args()

    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(process_window(args.window))
