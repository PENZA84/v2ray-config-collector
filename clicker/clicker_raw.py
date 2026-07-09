import asyncio
import os
import argparse
from playwright.async_api import async_playwright

# 🚫 ГЛОБАЛЬНЫЙ ЧЕРНЫЙ СПИСОК ДОМЕНОВ
BLOCK_DOMAINS = [
    'vk.com', 'vk.ru', 'dzen.ru', 'yandex.ru', 'mail.ru', 'ok.ru', 
    'youtube.com', 'youtu.be', 'github.blog', 'githubstatus.com',
    'api.github.com', 'avatars.githubusercontent.com', 'cdn.jsdelivr.net',
    'github-cloud.s3.amazonaws.com'
]

# 🗑️ ТОТАЛЬНАЯ БЛОКИРОВКА ТЕХНИЧЕСКОГО МУСОРА
# Сюда летят скрипты, лицензии, коммиты и системные страницы
BLOCK_PATHS = [
    '/commit/', '/collections', '/why-github', '/customer-stories',
    '/license', '.gitignore', 'readme.md', 'requirements.txt', 
    'sni_domains.json', '.py', 'get_subs', 'tg_proxy_main',
    'get_link.py', 'kuaizui.py', 'v2-clash.py', 'test.py'
]

# ⛽ БЕЛЫЙ СПИСОК РАСШИРЕНИЙ (Если у файла есть расширение, оно должно быть таким)
ALLOWED_EXTENSIONS = {'.json', '.yaml', '.yml', '.txt', '.list'}

def is_garbage(url):
    """Умное сито: отсекает грязь, бережет чистое топливо и файлы без расширений"""
    url_lower = url.lower()
    
    # 1. Жесткий отсев по доменам-паразитам
    if any(domain in url_lower for domain in BLOCK_DOMAINS):
        return True
        
    # 2. Жесткий отсев по системным путям и файлам кода
    if any(path in url_lower for path in BLOCK_PATHS):
        return True
        
    # 3. Чистка битых хвостов из логов (застрявшие кавычки, параметры юзеров)
    if 'quot;' in url_lower or 'user_id' in url_lower:
        return True

    # Вытаскиваем имя файла для анализа расширения
    url_parts = url_lower.split('/')
    filename = url_parts[-1] if url_parts else ""
    
    # Если в имени файла есть точка — проверяем расширение
    if '.' in filename:
        is_valid_ext = any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)
        if not is_valid_ext:
            return True  # Есть точка, но расширение левое (например .md или .py) -> Мусор
            
    # Если точки нет (как у Eternity или Long_term_subscription1) — файл признается ЧИСТЫМ топливом!
    return False

async def simple_grabber(page, target_url, final_urls):
    """Сборщик чистого топлива"""
    if is_garbage(target_url):
        return

    print(f"🔍 Сканируем источник: {target_url}", flush=True)
    try:
        await page.goto(target_url, timeout=15000, wait_until="domcontentloaded")
        
        links = await page.locator('a').all()
        for link in links:
            href = await link.get_attribute('href')
            if not href: 
                continue
            
            # Фильтруем ссылку еще до обработки
            if is_garbage(href):
                continue
            
            # Переводим обычные ссылки GitHub в чистый RAW формат
            full_url = href
            if "github.com" in href and "/blob/" in href:
                full_url = href.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            # Финальная проверка очищенной ссылки
            if not is_garbage(full_url):
                final_urls.add(full_url)
                    
    except Exception as e:
        print(f"⚠️ Ошибка на {target_url}: {e}", flush=True)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='clicker/profiles.txt', help='Входной файл')
    parser.add_argument('--output', type=str, default='clicker/raw_links.txt', help='Выходной файл')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Ошибка: {args.input} не найден!")
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        source_urls = [line.strip() for line in f if line.strip()]

    final_urls = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in source_urls:
            await simple_grabber(page, url, final_urls)

        await browser.close()

    # Сохраняем кристально чистый результат
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in sorted(final_urls):
            f.write(f"{link}\n")

    print(f"\n🚀 Завод успешно завершил цикл! Собрано чистого топлива: {len(final_urls)} шт.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
