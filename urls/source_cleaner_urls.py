import asyncio
import aiohttp
import os
import re

# === СИЛЬНЫЕ ФИЛЬТРЫ ===
BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']
BAD_KW = ['apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music', 'book', 'quote', 'steam', 'readme', 'youtube', 'boosty', 't.me/proxy', 'mtproto']

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"

            text = await resp.text()
            text_lower = text.lower()
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']):
                return "factory"

            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                return "factory"

            http_count = sum(1 for line in lines if line.startswith(('http://', 'https://')))
            if http_count >= 5:
                return "url_check"

            if len(text) > 1500 and re.search(r'[A-Za-z0-9+/=]{80,}', text):
                return "factory"

            return "filtered"
    except:
        return "dead"

def load_existing(file_path):
    if not os.path.exists(file_path):
        return set()
    with open(file_path, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}

async def main():
    input_file = 'urls/source_urls.txt'
    factory_file = 'urls/factory_valid.txt'
    url_checks_file = 'urls/url_checks.txt'
    filtered_file = 'urls/filtered_results.txt'
    dead_file = 'data/raw_incoming/deep_raw_collected.txt'

    if not os.path.exists(input_file):
        print("❌ source_urls.txt не найден")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

    print(f"🔍 Проверяю {len(urls)} ссылок...\n")

    # Загружаем существующие списки для избежания дубликатов
    existing_factory = load_existing(factory_file)
    existing_url_checks = load_existing(url_checks_file)
    existing_filtered = load_existing(filtered_file)

    factory = []
    url_checks = []
    filtered = []
    dead = []

    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls, 1):
            if i % 500 == 0:
                print(f"   Проверено {i}/{len(urls)}...")

            url_lower = url.lower()

            if any(ext in url_lower for ext in BAD_EXT) or any(kw in url_lower for kw in BAD_KW):
                dead.append(url)
                continue

            category = await deep_check(session, url)

            if category == "factory" and url not in existing_factory:
                factory.append(url)
            elif category == "url_check" and url not in existing_url_checks:
                url_checks.append(url)
            elif category == "dead":
                dead.append(url)
            elif url not in existing_filtered:
                filtered.append(url)

    # === ДОПОЛНЕНИЕ СПИСКОВ (не замена) ===
    with open(factory_file, 'a', encoding='utf-8') as f:
        if factory:
            f.write('\n'.join(factory) + '\n')

    with open(url_checks_file, 'a', encoding='utf-8') as f:
        if url_checks:
            f.write('\n'.join(url_checks) + '\n')

    with open(filtered_file, 'a', encoding='utf-8') as f:
        if filtered:
            f.write('\n'.join(filtered) + '\n')

    with open(dead_file, 'a', encoding='utf-8') as f:
        if dead:
            f.write("\n# === Новый мусор + dead ===\n")
            f.write("\n".join(dead) + "\n")

    # Очистка source_urls.txt
    open(input_file, 'w').close()
    print("🧹 source_urls.txt очищен после обработки")

    print(f"\n✅ Добавлено в этот раз:")
    print(f"   🏭 Factory: {len(factory)}")
    print(f"   🔗 Url_checks: {len(url_checks)}")
    print(f"   🗑 Filtered: {len(filtered)}")
    print(f"   💀 В бункер: {len(dead)}")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
