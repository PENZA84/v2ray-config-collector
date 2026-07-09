import asyncio
import os
import re
import argparse
from playwright.async_api import async_playwright

print("🚀 === clicker_raw.py [Браузерный Экстрактор + Имитация Клика V8.0] запущен ===")

# База системного мусора (остается для фильтрации итоговых ссылок)
BLOCK_DOMAINS = [
    'api.github.com', 'avatars.githubusercontent.com', 'camo.githubusercontent.com',
    'githubcopilot.com', 'schema.org', 'w3.org', 'collector.github.com',
    'desktop.github.com', 'docs.github.com', 'archiveprogram.github.com',
    'github.blog', 'star-history.com', 'img.shields.io', 'visitor-badge.laobi.icu',
    'dzen.ru', 'vk.com', 'vk.ru', 'youtube.com', 'youtu.be', 't.me/avencoreschat',
    'private-user-images.githubusercontent.com', 'opengraph.githubassets.com',
    'user-images.githubusercontent.com', 'play.google.com',
    'github.community', 'githubassets.com', 'maintainers.github.com', 
    'securitylab.github.com', 'skills.github.com', 'stars.github.com', 
    'support.github.com', 'windows.github.com', 'githubstatus.com'
]

BLOCK_KEYWORDS = [
    '/releases', '/download', '/changelog', '/issues', '/pulls', 
    '.github/workflows/', '/tags/',
    '/marketplace', '/mcp', '/open-source/', '/orgs/', '/partners', 
    '/pricing', '/resources', '/security', '/solutions', '/team', 
    '/topics', '/trending', '/trust-center'
]

SKIP_EXTENSIONS = [
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', 
    '.pdf', '.apk', '.exe', '.zip', '.rar', '.7z', '.dmg', '.git'
]

def convert_to_raw(url: str) -> str:
    """Если нашли ссылку на файл, делаем из неё прямой RAW-вариант"""
    if 'raw.githubusercontent.com' in url or 'blob_plain' in url:
        return url
    github_blob_match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)', url)
    if github_blob_match:
        user, repo, branch, filepath = github_blob_match.groups()
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{filepath}"
    return url

def is_github_folder(url: str) -> bool:
    """Проверяет, ведет ли ссылка на папку или корень репозитория"""
    url_lower = url.lower()
    if 'github.com' in url_lower:
        if '/tree/' in url_lower:
            return True
        match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/?$', url, re.IGNORECASE)
        if match:
            return True
    return False

async def browse_and_click(page, target_url, final_urls, visited_folders, depth=0):
    """Функция имитирует человека: открывает страницу, ищет папки, кликает и качает файлы"""
    if depth > 4 or target_url in visited_folders:
        return

    print(f"🕵️‍♂️ [Глубина {depth}] Имитируем переход человека на: {target_url}")
    
    try:
        # Переходим по ссылке в скрытом браузере
        await page.goto(target_url, timeout=60000, wait_until="networkidle")
        
        # 👤 Имитация человека: небольшая случайная пауза после загрузки страницы
        await asyncio.sleep(1.5)
        
        # Получаем весь отрендеренный JavaScript'ом контент страницы
        html_content = await page.content()
        
        # Собираем все стандартные ссылки со страницы
        found_urls = re.findall(r'https?://[^\s"\'><\\{}()\[\]]+', html_content)
        
        # Если мы находимся внутри репозитория/папки GitHub, собираем ссылки на файлы и подпапки
        if is_github_folder(target_url):
            visited_folders.add(target_url)
            
            # Находим все элементы ссылок на странице через селекторы браузера
            links = await page.locator('a').all()
            sub_folders_to_click = []
            
            for link in links:
                href = await link.get_attribute('href')
                if not href:
                    continue
                    
                full_url = f"https://github.com{href}" if href.startswith('/') else href
                full_url_lower = full_url.lower()
                
                # Фильтруем мусор сразу
                if any(keyword in full_url_lower for keyword in BLOCK_KEYWORDS) or any(domain in full_url_lower for domain in BLOCK_DOMAINS):
                    continue
                
                # Если нашли подпапку (/tree/), запоминаем её для клика
                if '/tree/' in full_url_lower and full_url not in visited_folders:
                    sub_folders_to_click.append((link, full_url))
                
                # Если нашли файл (/blob/), кидаем его в базу (потом превратим в RAW)
                elif '/blob/' in full_url_lower:
                    if not any(full_url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                        final_urls.add(convert_to_raw(full_url))

            # 🛠 ИМИТАЦИЯ КЛИКОВ ПО НАЙДЕННЫМ ПАПКАМ
            for folder_element, folder_url in sub_folders_to_click:
                if folder_url in visited_folders:
                    continue
                try:
                    print(f"🖱 Клик по папке: {folder_url.split('/')[-1]}")
                    # Скроллим к папке, как человек
                    await folder_element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    # Физически кликаем по ней внутри скрытого браузера!
                    await folder_element.click()
                    # Ждем, пока Гитхаб перерисует страницу
                    await page.wait_for_load_state("networkidle")
                    
                    # Рекурсивно сканируем новое содержимое
                    await browse_and_click(page, page.url, final_urls, visited_folders, depth + 1)
                    
                    # Возвращаемся назад, чтобы продолжить кликать по остальным папкам
                    await page.goto(target_url, wait_until="networkidle")
                    await asyncio.sleep(1)
                except Exception:
                    # Если клик не удался, просто попробуем зайти напрямую по URL папки
                    await browse_and_click(page, folder_url, final_urls, visited_folders, depth + 1)
        
        else:
            # Если это не папка Гитхаба, а обычный текстовый URL, просто парсим из него ссылки
            for url in found_urls:
                url = url.rstrip('.,;)精神\\/&\"\'')
                url_lower = url.lower()
                
                if not url or len(url) < 10:
                    continue
                if any(url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue
                if any(domain in url_lower for domain in BLOCK_DOMAINS):
                    continue
                if any(keyword in url_lower for keyword in BLOCK_KEYWORDS):
                    continue
                if url_lower in ['https://github.com', 'https://github.com/']:
                    continue
                    
                final_urls.add(url)
                
    except Exception as e:
        print(f"⚠️ Ошибка при обработке {target_url}: {e}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='clicker/profiles.txt')
    parser.add_argument('--output', type=str, default='clicker/raw_links.txt')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Исходный файл {args.input} не найден.")
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        source_urls = [line.strip() for line in f if line.strip()]

    if not source_urls:
        print("📭 Список profiles.txt пуст.")
        return

    print(f"📡 Запуск браузерного завода. Задач: {len(source_urls)} шт.")
    final_urls = set()
    visited_folders = set()

    # Запускаем скрытый движок Playwright
    async with async_playwright() as p:
        # headless=True означает, что браузер скрыт (работает в фоне без окон)
        browser = await p.chromium.launch(headless=True)
        
        # Создаем контекст с эмуляцией обычного ПК (User-Agent), чтобы Гитхаб не выдавал капчи
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Идем по нашему списку profiles.txt по очереди (чтобы имитация была естественной)
        for url in source_urls:
            await browse_and_click(page, url, final_urls, visited_folders)

        await browser.close()

    # Сохраняем добытое чистое золото
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in sorted(final_urls):
            f.write(f"{link}\n")

    print(f"💾 Завод завершил работу! Браузер закрыт. Результат в {args.output}. Собрано уникальных ссылок: {len(final_urls)}")

if __name__ == "__main__":
    asyncio.run(main())
