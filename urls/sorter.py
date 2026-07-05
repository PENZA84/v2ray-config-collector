import asyncio
import aiohttp
import os
import argparse
import re

print("=== sorter.py [Монолит V2.1] запущен ===")

# Список строго запрещенных расширений (добавлен .7z и .dmg)
BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3', '.js', '.css', '.sh', '.png', '.jpg', '.jpeg', '.gif', '.dmg', '.7z']

# Ключевые слова для фильтрации внутри deep_check
BAD_KW = [
    'apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music',
    'book', 'quote', 'steam', 'readme', 'boosty', 't.me/proxy', 'mtproto',
    'blog.', 'medium.com', 'substack', 'telegra.ph', 'happ.su', 'bintv.net', 'applnn.com',
    'tvlnn.com', 'techcrunch.com', 'gugu3.com/', 'donate', 'wikipedia',
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

            # 📌 ШАГ 1: Поиск живых прокси-протоколов (Основная задача Завода)
            has_proxies = any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://', 'socks://', 'socks5://'])
            if has_proxies:
                print(f" ✅ Factory (Живой протокол): {url}")
                return "factory"

            is_html = 'text/html' in resp.headers.get('Content-Type', '').lower() or any(tag in text_lower for tag in ['<!doctype html', '<html', '<body'])

            # 📌 ШАГ 2: Проверка на сырые списки / txt конфигурации
            if any(x in url_lower for x in ['/https.txt', '/proxies', '/free-proxy', '/proxy-list', '/clash', '/v2ray', '/xray', 'freeclashnode', 'clashnodes', 'uploads/', '.txt']):
                print(f" ✅ Factory (Raw/Txt подписка): {url}")
                return "factory"

            # Фикс ложных срабатываний: Base64 ищем ТОЛЬКО если это не стандартный HTML-сайт
            if not is_html and re.search(r'[A-Za-z0-9+/=]{60,}', text):
                print(f" ✅ Factory (Чистый Base64 маркер): {url}")
                return "factory"

            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                print(f" ✅ Factory (Subscription подпись): {url}")
                return "factory"

            # 📌 ШАГ 3: Определение медиа-потоков
            if ('.m3u' in url_lower or '.m3u8' in url_lower or '#extm3u' in text_lower):
                print(f" 📁 Miscellaneous (m3u): {url}")
                return "misc"

            # 📌 ШАГ 4: Поиск агрегаторов ссылок (url_checks) - Строго для не-HTML контента
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
            
            # 🛑 1. ИЗОЛЯЦИЯ ТЕЛЕГРАМА: Веб-версии каналов больше не пройдут в url_checks
            if 't.me/' in url_lower:
                print(f" 📁 Telegram Ссылка -> Строго в misc: {url}")
                misc.append(url)
                continue

            # 🛑 2. ФИЛЬТР НЕИНТЕРЕСНОЙ КРИПТЫ
            if any(c in url_lower for c in ['novadax.com', 'coinbase.com', 'cryptocurrency', 'cryptocurrencies', 'blockchain', 'coincap.io', 'bnbchain.org']):
                print(f" 🗑 Крипто-мусор -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            # 🛑 3. БЕЗУСЛОВНЫЙ БАН КОРПОРАТИВНОГО ШУМА, МЕДИА, АРХИВОВ И ТЕКСТОВЫХ ТАСК-МЕНЕДЖЕРОВ
            COMMON_JUNK = [
                'opera.com', 'ubuntu.com', 'ashampoo.com', 'twitter.com', 'x.com', 'rt.com', 
                'tf1.fr', 'testingcatalog.com', 'thegamer.com', 'tomsguide.com', 'safewise.com', 
                'techradar.com', 'startnext.com', 'pixiv.net', 'zap-mag.ru', 'zava.io', 'yoyapai.com',
                'amnezia.org/documentation', 'amnezia.org/ru/documentation', 'doc.qt.io', 
                'docs.ansible.com', 'docs.astral.sh', 'docs.aws.amazon.com', 'docs.breezometer.com',
                'docs.cherry-ai.com', 'docs.cloudbees.com', 'docs.coolercontrol.org', 'docs.gramaddict.org',
                'todo.txt', 'activefilerecovery'  # Фильтр для todo.txt и архивов восстановления
            ]
            if any(junk in url_lower for junk in COMMON_JUNK) or any(ext in url_lower for ext in BAD_EXT):
                print(f" 🗑 Безусловный мусор/документация -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            # 🛑 4. РАСПРЕДЕЛЕНИЕ ИИ-СЕРВИСОВ: Защита от попадания в Завод (factory_valid)
            AI_SERVICES = ['grok.com', 'rask.ai', 'openai.com', 'claude.ai', 'huggingface.co', 'gemini.com']
            is_raw_config = any(r in url_lower for r in ['/raw/', 'raw.githubusercontent', '.txt', '/proxies'])
            
            if any(ai in url_lower for ai in AI_SERVICES) and not is_raw_config:
                print(f" 🤖 AI Сервис -> Строго в filtered_results (Интерес): {url}")
                filtered.append(url)
                continue

            # 🛑 5. Стандартный черный список ключевых слов для страниц без raw-данных
            if any(kw in url_lower for kw in BAD_KW) and not is_raw_config:
                print(f" 🗑 Мусорное ключевое слово -> В БУНКЕР: {url}")
                deep_raw_collected.append(url)
                continue

            # Сетевой анализ для оставшихся потенциальных кандидатов
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
                    print(f" 🗑 Страница репозитория без raw-файлов -> В БУНКЕР: {url}")
                    deep_raw_collected.append(url)
                else:
                    filtered.append(url)

    # Запись по файлам
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
