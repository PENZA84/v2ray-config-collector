import asyncio
import os
import re
import argparse
from playwright.async_api import async_playwright

print("🚀 === clicker_raw.py [Детальный Трекинг Папок + Анти-мусор V9.0] запущен ===", flush=True)

# 🚫 КРИТИЧЕСКИЙ ЧЕРНЫЙ СПИСОК ДОМЕНОВ ДЛЯ ФИЛЬТРАЦИИ МУСОРА
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
    'support.github.com', 'windows.github.com', 'githubstatus.com',
    'cdn.jsdelivr.net'
]

# 🚫 СЛОВА-ПАРАЗИТЫ (Сюда добавили /features, /enterprise, /premium-support, /startups и т.д.)
BLOCK_KEYWORDS = [
    '/releases', '/download', '/changelog', '/issues', '/pulls', 
    '.github/workflows/', '/tags/', '/marketplace', '/mcp', '/open-source/', 
    '/orgs/', '/partners', '/pricing', '/resources', '/security', '/solutions', 
    '/team', '/topics', '/trending', '/trust-center',
    '/features', '/enterprise', '/premium-support', '/startups', '/copilot', '/codespaces', '/code-review'
]

SKIP_EXTENSIONS = [
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', 
    '.pdf', '.apk', '.exe', '.zip', '.rar', '.7z', '.dmg', '.git'
]

def parse_repo_and_path(url: str) -> str:
    """Красиво вытаскивает название репозитория и текущий путь/файл из ссылки для логов"""
    match = re.search(r'github\.com/([^/]+/[^/]+)(?:/(?:tree|blob)/[^/]+/(.*))?', url, re.IGNORECASE)
    if match:
        repo, path = match.groups()
        if path:
            return f"📂 [{repo}] -> 📄 {path}"
        return f"📂 [{repo}] (Корень)"
    # Для raw ссылок
    raw_match = re.search(r'raw\.githubusercontent\.com/([^/]+/[^/]+)/[^/]+/(.*)', url, re.IGNORECASE)
    if raw_match:
        repo, path = raw_match.groups()
        return f"📂 [{repo}] -> 📄 {path} (RAW)"
    return url

def convert_to_raw(url: str) -> str:
    if 'raw.githubusercontent.com' in url or 'blob_plain' in url:
        return url
    github_blob_match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)', url)
    if github_blob_match:
        user, repo, branch, filepath = github_blob_match.groups()
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{filepath}"
    return url

def is_github_folder(url: str) -> bool:
    url_lower = url.lower()
    if 'github.com' in url_lower:
        if '/tree/' in url_lower:
            return True
        match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/?$', url, re.IGNORECASE)
        if match:
            return True
    return False

async def browse_and_click(page, target_url, final_urls, visited_folders, depth=0):
    if depth > 4 or target_url in visited_folders:
        return

    # 🛠 ЖЕСТКАЯ ПРОВЕРКА НА СИСТЕМНЫЙ МУСОР (features, enterprise и т.д.) ПЕРЕД ПЕРЕХОДОМ
    url_lower = target_url.lower()
    if any(keyword in url_lower for keyword in BLOCK_KEYWORDS) or any(domain in url_lower for domain in BLOCK_DOMAINS):
        return

    # Выводим красивый человеческий путь вместо длинного URL
    pretty_path = parse_repo_and_path(target_url)
    print(f"   🕵️‍♂️ [Глубина {depth}] Изучаем: {pretty_path}", flush=True)
    
    try:
        await page.goto(target_url, timeout=60000, wait_until="networkidle")
        await asyncio.sleep(1.0)
        
        html_content = await page.content()
        found_urls = re.findall(r'https?://[^\s"\'><\\{}()\[\]]+', html_content)
        
        if is_github_folder(target_url):
            visited_folders.add(target_url)
            
            links = await page.locator('a').all()
            sub_folders_to_click = []
            
            for link in links:
                href = await link.get_attribute('href')
                if not href:
                    continue
                    
                full_url = f"https://github.com{href}" if href.startswith('/') else href
                full_url_lower = full_url.lower()
                
                # Фильтруем мусорные ссылки внутри страницы, чтобы не кликать по кнопкам Гитхаба
                if any(keyword in full_url_lower for keyword in BLOCK_KEYWORDS) or any(domain in full_url_lower for domain in BLOCK_DOMAINS):
                    continue
                
                if '/tree/' in full_url_lower and full_url not in visited_folders:
                    sub_folders_to_click.append((link, full_url))
                elif '/blob/' in full_url_lower:
                    if not any(full_url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                        final_urls.add(convert_to_raw(full_url))

            for folder_element, folder_url in sub_folders_to_click:
                if folder_url in visited_folders:
                    continue
                try:
                    folder_name = folder_url.split('/')[-1]
                    print(f"   🖱 Клик по подпапке -> [{folder_name}]", flush=True)
                    await folder_element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.3)
                    await folder_element.click()
                    await page.wait_for_load_state("networkidle")
                    
                    await browse_and_click(page, page.url, final_urls, visited_folders, depth + 1)
                    await page.goto(target_url, wait_until="networkidle")
                    await asyncio.sleep(0.5)
                except Exception:
                    await browse_and_click(page, folder_url, final_urls, visited_folders, depth + 1)
        else:
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
        pass

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='clicker/profiles.txt')
    parser.add_argument('--output', type=str, default='clicker/raw_links.txt')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Исходный файл {args.input} не найден.", flush=True)
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        source_urls = []
        for line in f:
            line_clean = line.strip()
            if not line_clean:
                continue
            line_lower = line_clean.lower()
            # Ультра-фильтр: убираем мусорные строки прямо на этапе загрузки из profiles.txt
            if any(k in line_lower for k in BLOCK_KEYWORDS) or any(d in line_lower for d in BLOCK_DOMAINS):
                continue
            source_urls.append(line_clean)

    total_sources = len(source_urls)
    if not source_urls:
        print("📭 Список profiles.txt пуст или полностью отфильтрован от мусора.", flush=True)
        return

    print(f"📡 Завод отфильтровал мусор. Загружено чистых источников: {total_sources}", flush=True)
    final_urls = set()
    visited_folders = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        for index, url in enumerate(source_urls, 1):
            repo_title = parse_repo_and_path(url)
            print(f"\n🔄 [{index}/{total_sources}] Добыча на объекте: {repo_title}", flush=True)
            
            await browse_and_click(page, url, final_urls, visited_folders)
            print(f"✨ Всего уникальных RAW-ссылок в базе: {len(final_urls)}", flush=True)

        await browser.close()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in sorted(final_urls):
            f.write(f"{link}\n")

    print(f"\n💾 [Завод успешно завершил цикл!] Результат в {args.output}. Добыто чистых прокси-ссылок: {len(final_urls)} шт.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
