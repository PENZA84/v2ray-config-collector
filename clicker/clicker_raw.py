import asyncio
import aiohttp
import os
import re
import argparse

print("🚀 === clicker_raw.py [Сборщик сырых ссылок] запущен ===")

# Расширенный список системного хлама и маркетинга (больше никакого мусора в сырье!)
BLOCK_DOMAINS = [
    'api.github.com', 'avatars.githubusercontent.com', 'camo.githubusercontent.com',
    'githubcopilot.com', 'schema.org', 'w3.org', 'collector.github.com',
    'desktop.github.com', 'docs.github.com', 'archiveprogram.github.com',
    'github.blog', 'github-cloud.s3.amazonaws.com', 'opengraph.githubassets.com',
    'private-user-images.githubusercontent.com', 'play.google.com', 'apps.apple.com',
    'python.org', 'opensource.org'
]

# Сюда улетают все приложения, архивы и веб-стили. .yaml, .yml и .txt НЕ ТРОГАЕМ!
SKIP_EXTENSIONS = [
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', 
    '.pdf', '.apk', '.exe', '.zip', '.rar', '.7z', '.dmg'
]

def convert_to_raw(url: str) -> str:
    if 'raw.githubusercontent.com' in url or 'blob_plain' in url:
        return url
    github_blob_match = re.match(r'https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)', url)
    if github_blob_match:
        user, repo, branch, filepath = github_blob_match.groups()
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{filepath}"
    return url

async def fetch_clean_urls(session, target_url: str):
    raw_url = convert_to_raw(target_url)
    try:
        # УВЕЛИЧЕНО ДО 90 СЕКУНД: Спокойно переваривает тяжелые архивы, папки и огромные файлы вилок
        async with session.get(raw_url, timeout=90, allow_redirects=True) as resp:
            if resp.status != 200:
                return []

            text = await resp.text(errors='ignore')
            
            # Строгий сбор ссылок без мусорных хвостов гитхабовского кода
            found_urls = re.findall(r'https?://[^\s"\'><\\{}()\[\]]+', text)
            clean_set = set()

            for url in found_urls:
                url = url.rstrip('.,;)精神\\/')
                url_lower = url.lower()

                if not url or len(url) < 10:
                    continue
                if any(url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue
                if any(domain in url_lower for domain in BLOCK_DOMAINS):
                    continue
                if url_lower in ['https://github.com', 'https://github.com/']:
                    continue
                
                # Жесткий отсев страниц релизов, тегов, обновлений и загрузок софта
                if any(garbage in url_lower for garbage in ['/releases/', '/changelog', '/tags/', '/download']):
                    continue

                clean_set.add(url)
            return list(clean_set)
    except Exception:
        return []

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

    print(f"📡 Сбор базы из источников: {len(source_urls)} шт.")
    final_urls = set()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_clean_urls(session, url) for url in source_urls]
        results = await asyncio.gather(*tasks)
        for links in results:
            for link in links:
                final_urls.add(link)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in sorted(final_urls):
            f.write(f"{link}\n")

    print(f"💾 Готово! Новый список сырых ссылок сохранен in {args.output}. Всего: {len(final_urls)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
