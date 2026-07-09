import asyncio
import aiohttp
import os
import re
import argparse

print("🚀 === clicker_raw.py [Заводской Экстрактор + Блок Медиа-Мусора V5.9] запущен ===")

# Полный список системного мусора (добавили пользовательские картинки Гитхаба)
BLOCK_DOMAINS = [
    'api.github.com', 'avatars.githubusercontent.com', 'camo.githubusercontent.com',
    'githubcopilot.com', 'schema.org', 'w3.org', 'collector.github.com',
    'desktop.github.com', 'docs.github.com', 'archiveprogram.github.com',
    'github.blog', 'star-history.com', 'img.shields.io', 'visitor-badge.laobi.icu',
    'dzen.ru', 'vk.com', 'vk.ru', 'youtube.com', 'youtu.be', 't.me/avencoreschat',
    # Блокировка картинок: из логов, обложек и пользовательских вложений в Issues/Readme
    'private-user-images.githubusercontent.com', 'opengraph.githubassets.com',
    'user-images.githubusercontent.com',
    # Вспомогательные сервисы
    'github.community', 'githubassets.com', 'maintainers.github.com', 
    'securitylab.github.com', 'skills.github.com', 'stars.github.com', 
    'support.github.com', 'windows.github.com', 'githubstatus.com'
]

# КЛЮЧЕВЫЕ СЛОВА-ПАРАЗИТЫ: релизы, ветки, воркфлоу
BLOCK_KEYWORDS = [
    '/releases', '/download', '/changelog', '/issues', '/pulls', 
    '.github/workflows/', '/tree/', '/tags/'
]

# ИСКЛЮЧЕНИЯ: Расширения файлов, которые летят в помойку сразу
SKIP_EXTENSIONS = [
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', 
    '.pdf', '.apk', '.exe', '.zip', '.rar', '.7z', '.dmg', '.git'
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
        async with session.get(raw_url, timeout=90, allow_redirects=True) as resp:
            if resp.status != 200:
                return []

            text = await resp.text(errors='ignore')
            
            # Текстовый заслон от системного кода GitHub Actions и разметки Clash
            if any(marker in text for marker in ['workflow_dispatch:', 'runs-on:', 'jobs:', 'health-check:', 'proxy-groups:', 'steps:']):
                return []

            found_urls = re.findall(r'https?://[^\s"\'><\\{}()\[\]]+', text)
            clean_set = set()

            for url in found_urls:
                # Очищаем хвосты гитхабовского лога
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

                # Дополнительный фильтр ложных YAML/YML генераторов
                if url_lower.endswith('.yaml') or url_lower.endswith('.yml'):
                    if any(k in url_lower for k in ['clash', 'provider', 'v2rayse.com', '/update/']):
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

    print(f"💾 Готово! Пользовательские скриншоты с user-images забанены. Результат в {args.output}. Всего: {len(final_urls)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
