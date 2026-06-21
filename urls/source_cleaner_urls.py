import asyncio
import aiohttp
import os
import re

# Исключения медиа, архивов и документов
EXCLUDED_EXTENSIONS = [
    '.mp4', '.zip', '.apk', '.rar', '.exe', '.tar.gz',
    '.7z', '.pdf', '.md', '.mp3', '.png', '.jpg', '.jpeg', '.gif', '.tar'
]
EXCLUDED_KEYWORDS = ['release', 'релиз', 'download', 'archive']

async def check_link(session, url):
    url_lower = url.lower().strip()
    if not url_lower.startswith(('http://', 'https://')):
        return ('trash', url)

    # 1. Специальные проверки
    if '_url_check' in url_lower:
        return ('url_checks', url)

    # Фильтрация по расширениям
    if any(ext in url_lower for ext in EXCLUDED_EXTENSIONS):
        return ('trash', url)

    # Фильтрация по ключевым словам
    if any(kw in url_lower for kw in EXCLUDED_KEYWORDS):
        return ('trash', url)

    try:
        async with session.get(url, timeout=10, allow_redirects=True) as response:
            if response.status != 200:
                return ('trash', url)

            # Читаем текст (с лимитом, чтобы не упасть на огромных файлах)
            text = await response.text()
            text_lower = text.lower()
            text_len = len(text)

            # === УЛУЧШЕННЫЕ ПРОВЕРКИ ДЛЯ ЗАВОДА ===
            # 1. Классические протоколы
            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'socks5://']):
                return ('factory', url)

            # 2. Признаки хорошей подписки (Clash/Xray/V2Ray)
            subscription_signs = ['#profile-title', '#profile-update-interval', '#subscription-userinfo', 
                                  'subscription', 'clash', 'xray', 'v2ray', 'shadowrocket']
            if any(sign in text_lower for sign in subscription_signs):
                return ('factory', url)

            # 3. Длинный чистый текст (Base64 или список прокси)
            if text_len > 500 and '<html' not in text_lower and '<body' not in text_lower and '<!doctype' not in text_lower:
                # Проверка на Base64-like контент
                if re.search(r'[A-Za-z0-9+/]{50,}', text):
                    return ('factory', url)

            return ('trash', url)

    except asyncio.TimeoutError:
        return ('trash', url)
    except Exception as e:
        # print(f"Ошибка при проверке {url}: {e}")  # раскомментировать при отладке
        return ('trash', url)


async def main():
    dir_path = 'urls'
    input_file = os.path.join(dir_path, 'source_urls.txt')
   
    output_factory = os.path.join(dir_path, 'factory_valid.txt')
    output_url_checks = os.path.join(dir_path, 'url_checks.txt')
    output_filtered = os.path.join(dir_path, 'filtered_results.txt')
   
    os.makedirs(dir_path, exist_ok=True)
   
    if not os.path.exists(input_file):
        print("❌ Файл source_urls.txt не найден!")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

    if not urls:
        print("⚠ Нет ссылок для обработки.")
        return

    print(f"🔍 Проверяю {len(urls)} ссылок...")

    async with aiohttp.ClientSession() as session:
        tasks = [check_link(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    categorized = {'factory': [], 'url_checks': [], 'trash': []}
    for cat, url in results:
        categorized[cat].append(url)

    # Запись результатов
    with open(output_factory, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categorized['factory']) + '\n' if categorized['factory'] else '')

    with open(output_url_checks, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categorized['url_checks']) + '\n' if categorized['url_checks'] else '')

    with open(output_filtered, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categorized['trash']) + '\n' if categorized['trash'] else '')

    print(f"✅ Готово!")
    print(f"   🏭 Factory (для Трона): {len(categorized['factory'])} ссылок")
    print(f"   🔍 Url_checks: {len(categorized['url_checks'])}")
    print(f"   🗑 Trash: {len(categorized['trash'])}")


if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
