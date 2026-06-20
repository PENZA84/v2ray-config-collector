import asyncio
import aiohttp
import os

# Исключения медиа, архивов и документов
EXCLUDED_EXTENSIONS = [
    '.mp4', '.zip', '.apk', '.rar', '.exe', '.tar.gz', 
    '.7z', '.pdf', '.md', '.mp3', '.png', '.jpg', '.jpeg'
]
EXCLUDED_KEYWORDS = ['release', 'релиз']

async def check_link(session, url):
    url_lower = url.lower()
    
    # 1. Фильтр по вхождению 'url' в название или путь ссылки
    if 'url' in url_lower:
        return ('url_checks', url)
        
    # 2. Фильтрация по расширениям файлов
    if any(ext in url_lower for ext in EXCLUDED_EXTENSIONS):
        return ('trash', url)
        
    # 3. Фильтрация по ключевым словам
    if any(kw in url_lower for kw in EXCLUDED_KEYWORDS):
        return ('trash', url)

    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                text = await response.text()
                text_lower = text.lower()
                
                # Проверка наличия прокси-протоколов
                if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://']):
                    return ('factory', url)
                
                # Проверка на чистый Base64 (без HTML-разметки)
                elif '<html' not in text_lower and len(text) > 20:
                    return ('factory', url)
                
                else:
                    return ('trash', url)
            else:
                return ('trash', url)
    except:
        return ('trash', url)

async def main():
    dir_path = 'urls'
    input_file = os.path.join(dir_path, 'source_urls.txt')
    
    output_factory = os.path.join(dir_path, 'factory_valid.txt')
    output_url_checks = os.path.join(dir_path, 'url_checks.txt')
    output_filtered = os.path.join(dir_path, 'filtered_results.txt')
    
    if not os.path.exists(input_file):
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith('http')]

    if not urls:
        return

    async with aiohttp.ClientSession() as session:
        tasks = [check_link(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    categorized = {
        'factory': [],
        'url_checks': [],
        'trash': []
    }

    for cat, url in results:
        categorized[cat].append(url)

    # Запись результатов
    with open(output_factory, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categorized['factory']) + '\n')

    with open(output_url_checks, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categorized['url_checks']) + '\n')

    with open(output_filtered, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categorized['trash']) + '\n')

    # Очистка входного списка
    open(input_file, 'w').close()

if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
