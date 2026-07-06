import asyncio
import aiohttp
import os
import re
import argparse

print("=== clicker_raw.py [Сборщик чистых прокси и подписок] запущен ===")

# Полностью исключаем домены со спамом и статистикой (из скриншотов 1816, 1820)
BLOCK_DOMAINS = [
    'youtube.com', 'youtu.be', 'api.github.com', 'avatars.githubusercontent.com',
    'camo.githubusercontent.com', 'githubcopilot.com', 'schema.org', 'w3.org',
    'collector.github.com', 'google.com', 'yandex', '.ru'
]

# Исключаем загрузку тяжелой статики
SKIP_EXTENSIONS = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.pdf']

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
        async with session.get(raw_url, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                return []

            text = await resp.text(errors='ignore')
            # Поиск любых строк, похожих на ссылки
            found_urls = re.findall(r'https?://[^\s"\'>]+', text)
            clean_set = set()

            for url in found_urls:
                # Жесткая очистка от остатков HTML-тегов и экранирования строк
                for junk in ['&quot;', '\\u003c', '</a', '\\u003e', '\\', '"', "'", '<', '>', '}', '{', ']', '[']:
                    if junk in url:
                        url = url.split(junk)[0]
                
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

                clean_set.add(url)
            return list(clean_set)
    except Exception:
        return []

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='clicker/profiles.txt')
    parser.add_argument('--output', type=str, default='clicker/extracted_urls.txt')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Исходный файл {args.input} не найден.")
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        source_urls = [line.strip() for line in f if line.strip()]

    if not source_urls:
        print("Список profiles.txt пуст.")
        return

    print(f"Обработка источников: {len(source_urls)} шт.")
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

    print(f"💾 Готово! Сгенерирован чистый список без мусора. Ссылок: {len(final_urls)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
