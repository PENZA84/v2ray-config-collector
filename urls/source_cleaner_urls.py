import asyncio
import aiohttp
import os
import re

# Фильтры явного мусора
BAD_EXT = ['.lua', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']
BAD_KW = ['apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music', 'book', 'quote']

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"

            text = await resp.text()
            text_lower = text.lower()
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            # 1. Прямые протоколы → factory_valid.txt
            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']):
                return "factory"

            # 2. Признаки хорошей подписки
            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                return "factory"

            # 3. Много http/https ссылок внутри файла → interesting.txt
            http_count = sum(1 for line in lines if line.startswith(('http://', 'https://')))
            if http_count >= 5:
                return "interesting"

            # 4. Большой Base64-like файл
            if len(text) > 1500 and re.search(r'[A-Za-z0-9+/=]{80,}', text):
                return "factory"

            return "filtered"
    except:
        return "dead"

async def main():
    input_file = 'urls/source_urls.txt'
    factory_file = 'urls/factory_valid.txt'
    interesting_file = 'urls/interesting.txt'
    filtered_file = 'urls/filtered_results.txt'
    checks_file = 'urls/url_checks.txt'
    dead_file = 'data/raw_incoming/deep_raw_collected.txt'

    if not os.path.exists(input_file):
        print("❌ source_urls.txt не найден")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

    print(f"🔍 Проверяю {len(urls)} ссылок...")

    factory = []
    interesting = []
    filtered = []
    checks = []
    dead = []

    async with aiohttp.ClientSession() as session:
        for url in urls:
            # Убрал автоматическое определение по названию _url_check
            # Теперь всё решает содержимое

            category = await deep_check(session, url)

            if category == "factory":
                factory.append(url)
            elif category == "interesting":
                interesting.append(url)
            elif category == "dead":
                dead.append(url)
            else:
                filtered.append(url)

    # Сохранение
    with open(factory_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(factory) + '\n' if factory else '')
    with open(interesting_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(interesting) + '\n' if interesting else '')
    with open(filtered_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered) + '\n' if filtered else '')
    with open(checks_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(checks) + '\n' if checks else '')

    with open(dead_file, 'a', encoding='utf-8') as f:
        if dead:
            f.write("\n# === Новые мёртвые ===\n")
            f.write("\n".join(dead) + "\n")

    print(f"✅ Factory (протоколы): {len(factory)}")
    print(f"📌 Interesting (много ссылок внутри): {len(interesting)}")
    print(f"🗑 Filtered: {len(filtered)}")
    print(f"🔍 Url_checks: {len(checks)}")
    print(f"💀 Dead: {len(dead)}")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
