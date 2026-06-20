import asyncio
import aiohttp
import os
import base64

EXCLUDED_EXTENSIONS = [
    '.mp4', '.zip', '.apk', '.rar', '.exe', '.tar.gz', 
    '.7z', '.pdf', '.md', '.mp3', '.png', '.jpg', '.jpeg'
]
EXCLUDED_KEYWORDS = ['release', 'релиз']

def is_valid_base64_sub(text):
    """Проверяет, является ли текст реальной Base64 подпиской с протоколами внутри"""
    clean_text = text.strip().replace('\r', '').replace('\n', '').replace(' ', '')
    if len(clean_text) < 20:
        return False
    try:
        # Пробуем декодировать строку
        decoded = base64.b64decode(clean_text).decode('utf-8', errors='ignore')
        decoded_lower = decoded.lower()
        # Если внутри декодированного текста есть прокси-протоколы — это валид
        return any(p in decoded_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'shadowsocks://', 'tuic://', 'hy2://'])
    except:
        return False

async def check_link(session, url):
    url_lower = url.lower()
    
    if 'url' in url_lower:
        return ('url_checks', url)
        
    if any(ext in url_lower for ext in EXCLUDED_EXTENSIONS):
        return ('trash', url)
        
    if any(kw in url_lower for kw in EXCLUDED_KEYWORDS):
        return ('trash', url)

    try:
        # Таймаут 4 секунды, чтобы отсекать зависающие IP как на скриншоте
        async with session.get(url, timeout=4) as response:
            if response.status == 200:
                text = await response.text()
                text_lower = text.lower()
                
                # 1. Проверка на открытые протоколы в тексте
                if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://']):
                    return ('factory', url)
                
                # 2. Проверка на валидный, расшифруемый Base64-пакет
                elif is_valid_base64_sub(text):
                    return ('factory', url)
                
                # Все остальное (заглушки панелей, текст, HTML) летит в мусор
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

    # Запись результатов (дописывание в конец файлов, чтобы не затирать старое)
    for key, file_path in [('factory', output_factory), ('url_checks', output_url_checks), ('trash', output_filtered)]:
        if categorized[key]:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(categorized[key]) + '\n')

    # Полная очистка входного буфера
    open(input_file, 'w').close()

if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
