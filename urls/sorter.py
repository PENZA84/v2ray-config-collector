import asyncio
import aiohttp
import os
import re
import sys
import argparse

BATCH_SIZE = 20000

BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']
BAD_KW = [
    'apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook',
    'music', 'book', 'quote', 'steam', 'readme', 'youtube', 'boosty', 't.me/proxy',
    'mtproto', 'blog.', 'medium.com', 'substack', 'telegra.ph', 'happ.su', 'bintv.net',
    'applnn.com', 'tvlnn.com', 'techcrunch.com', 'google.com', 'translate.google',
    'microsoft.com', 'bing.com', 'outlook.com', 'github.com', 'gitlab.com', 
    'bitbucket.org', 'anthropic.com', 'instagram.com', 'videosearch', 'wikipedia.org', 
    'wiki', 'donate', 'gugu3.com'
]

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"
            text = await resp.text()
            text_lower = text.lower()
            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']):
                return "factory"
            return "filtered"
    except:
        return "dead"

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--window', type=int, default=0, help="Номер окна (0 = все)")
    args = parser.parse_args()

    chunks_dir = 'urls/urls'
    factory_file = 'urls/factory_valid.txt'
    url_checks_file = 'urls/url_checks.txt'
    dead_file = 'data/raw_incoming/deep_raw_collected.txt'

    chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.startswith('chunk_')])

    print(f"🔄 [Окно №{args.window}] Запуск обработки...")

    all_factory = []
    all_url_checks = []
    all_dead = []

    async with aiohttp.ClientSession() as session:
        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunks_dir, chunk_file)
            print(f"   📂 {chunk_file}")

            with open(chunk_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

            for url in urls:
                url_lower = url.lower()
                if any(ext in url_lower for ext in BAD_EXT) or any(kw in url_lower for kw in BAD_KW):
                    all_dead.append(url)
                    continue

                category = await deep_check(session, url)
                if category == "factory":
                    all_factory.append(url)
                else:
                    all_url_checks.append(url)

    # Склейка
    with open(factory_file, 'a', encoding='utf-8') as f:
        if all_factory:
            f.write('\n'.join(all_factory) + '\n')

    with open(url_checks_file, 'a', encoding='utf-8') as f:
        if all_url_checks:
            f.write('\n'.join(all_url_checks) + '\n')

    with open(dead_file, 'a', encoding='utf-8') as f:
        if all_dead:
            f.write("\n# === Новый мусор + dead ===\n")
            f.write("\n".join(all_dead) + "\n")

    print(f"✅ [Окно №{args.window}] Завершено | Factory: {len(all_factory)} | Url_checks: {len(all_url_checks)}")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
