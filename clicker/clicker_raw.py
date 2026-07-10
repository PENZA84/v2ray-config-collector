import asyncio
import os
import re
import argparse
from playwright.async_api import async_playwright

print("🚀 === clicker_raw.py [Обновлено: исключены папки без топлива] ===", flush=True)

# 🚫 ЧЕРНЫЙ СПИСОК ДОМЕНОВ
BLOCK_DOMAINS = [
    'api.github.com', 'avatars.githubusercontent.com', 'camo.githubusercontent.com',
    'githubcopilot.com', 'schema.org', 'w3.org', 'collector.github.com',
    'desktop.github.com', 'docs.github.com', 'archiveprogram.github.com',
    'github.blog', 'star-history.com', 'img.shields.io', 'visitor-badge.laobi.icu',
    'dzen.ru', 'vk.com', 'vk.ru', 'youtube.com', 'youtu.be', 'private-user-images.githubusercontent.com',
    'opengraph.githubassets.com', 'user-images.githubusercontent.com', 'play.google.com',
    'github.community', 'githubassets.com', 'maintainers.github.com',
    'securitylab.github.com', 'skills.github.com', 'stars.github.com',
    'support.github.com', 'windows.github.com', 'githubstatus.com', 'cdn.jsdelivr.net'
]

# 🚫 ЧЕРНЫЙ СПИСОК ПУТЕЙ — папки, где нет протоколов и конфигов
BLOCK_KEYWORDS = [
    '.github/workflows', 'releases', '/release',  '/__pycache__ ', '/download', '/changelog', '/issues', '/pulls',
    '/tags/', '/marketplace', '/mcp', '/open-source/', '/orgs/', '/partners', '/pricing', '/resources', '/security', '/solutions',
    '/team', '/topics', '/trending', '/trust-center', '/features', '/enterprise', '/premium-support', '/startups', '/copilot', '/codespaces', '/code-review'
]

SKIP_EXTENSIONS = [
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2',
    '.pdf', '.apk', '.exe', '.zip', '.rar', '.7z', '.dmg', '.git', '.api', '.images'
]

def parse_repo_and_path(url: str) -> str:
    match = re.search(r'github\.com/([^/]+/[^/]+)(?:/(?:tree|blob)/[^/]+/(.*))?', url, re.IGNORECASE)
    if match:
        repo, path = match.groups()
        return f"📂 [{repo}] -> 📄 {path}" if path else f"📂 [{repo}] (Корень)"
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

    url_lower = target_url.lower()
    if any(keyword in url_lower for keyword in BLOCK_KEYWORDS) or any(domain in url_lower for domain in BLOCK_DOMAINS):
        return

    pretty_path = parse_repo_and_path(target_url)
    print(f"   🕵️ [Глубина {depth}] Открываем: {pretty_path}", flush=True)

    try:
        await page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(0.25)

        html_content = await page.content()

        if is_github_folder(target_url):
            visited_folders.add(target_url)
            links = await page.locator('a').all()
            sub_folder_urls = []

            for link in links:
                href = await link.get_attribute('href')
                if not href:
                    continue
                full_url = f"https://github.com{href}" if href.startswith('/') else href
                full_url_lower = full_url.lower()

                if any(keyword in full_url_lower for keyword in BLOCK_KEYWORDS) or any(domain in full_url_lower for domain in BLOCK_DOMAINS):
                    continue

                if '/tree/' in full_url_lower and full_url not in visited_folders:
                    if full_url not in sub_folder_urls:
                        sub_folder_urls.append(full_url)
                elif '/blob/' in full_url_lower:
                    if not any(full_url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                        final_urls.add(convert_to_raw(full_url))

            for folder_url in sub_folder_urls:
                if folder_url in visited_folders:
                    continue
                try:
                    relative_href = folder_url.replace("https://github.com", "")
                    folder_element = page.locator(f'a[href="{relative_href}"]').first

                    await folder_element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.1)
                    await folder_element.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(0.15)

                    await browse_and_click(page, page.url, final_urls, visited_folders, depth + 1)

                    await page.goto(target_url, wait_until="domcontentloaded")
                    await asyncio.sleep(0.15)
                except Exception:
                    await browse_and_click(page, folder_url, final_urls, visited_folders, depth + 1)
        else:
            found_urls = re.findall(r'https?://[^\s"\'><\\{}()\[\]]+', html_content)
            for url in found_urls:
                url = url.rstrip('.,;)\\/&"\'')
                url_lower = url.lower()
                if not url or len(url) < 10 or any(url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue
                if any(domain in url_lower for domain in BLOCK_DOMAINS) or any(keyword in url_lower for keyword in BLOCK_KEYWORDS):
                    continue
                final_urls.add(url)

    except Exception as e:
        print(f"   ⚠️ Ошибка на {pretty_path}: {e}", flush=True)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='clicker/profiles.txt')
    parser.add_argument('--output', type=str, default='clicker/raw_links.txt')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Файл {args.input} не найден.", flush=True)
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        source_urls = [line.strip() for line in f if line.strip()]

    source_urls = [u for u in source_urls if not any(k in u.lower() for k in BLOCK_KEYWORDS) and not any(d in u.lower() for d in BLOCK_DOMAINS)]

    if not source_urls:
        print("📭 Список источников пуст.", flush=True)
        return

    print(f"📡 Поставщик запущен. Источников: {len(source_urls)}", flush=True)
    final_urls = set()
    visited_folders = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            java_script_enabled=True
        )
        page = await context.new_page()

        for idx, url in enumerate(source_urls, 1):
            print(f"\n🔄 [{idx}/{len(source_urls)}] Обрабатываем: {parse_repo_and_path(url)}", flush=True)
            await browse_and_click(page, url, final_urls, visited_folders)
            print(f"✨ Собрано: {len(final_urls)}", flush=True)

        await browser.close()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(final_urls)) + "\n")

    print(f"\n💾 Готово! Сохранено: {args.output} | Всего: {len(final_urls)} шт.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
