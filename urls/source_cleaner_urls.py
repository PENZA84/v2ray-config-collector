import asyncio
import aiohttp
import os
import re

# === СИЛЬНЫЕ ФИЛЬТРЫ ===
BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']
BAD_KW = ['apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music', 'book', 'quote', 'steam', 'readme']

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"

            text = await resp.text()
            text_lower = text.lower()
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            # === СТРОГОЕ УСЛОВИЕ ДЛЯ FACTORY ===
            # Должны быть прямые протоколы
            protocols = ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://']
            if any(p in text_lower for p in protocols):
                return "factory"

            # Дополнительные признаки хорошей подписки
            if any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo']):
                return "factory"

            # Большой Base64-контент
            if len(text) > 2000 and re.search(r'[A-Za-z0-9+/=]{80,}', text):
                return "factory"

            # Если это Clash-правила, но без протоколов — в url_checks
            if 'clash' in text_lower and any(line.startswith(('http://', 'https://')) for line in lines):
                return "url_check"

            return "filtered"
    except:
        return "dead"

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

    print(f"🔍 Проверяю {len(urls)} ссылок...")

    factory = []
    url_checks = []
    filtered = []
    dead = []

    async with aiohttp.ClientSession() as session:
        for url in urls:
            url_lower = url.lower()

            if any(ext in url_lower for ext in BAD_EXT) or any(kw in url_lower for kw in BAD_KW):
                dead.append(url)
                continue

            category = await deep_check(session, url)

            if category == "factory":
                factory.append(url)
            elif category == "url_check":
                url_checks.append(url)
            elif category == "dead":
                dead.append(url)
            else:
                filtered.append(url)

    # Сохранение
    with open(factory_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(factory) + '\n' if factory else '')
    with open(url_checks_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(url_checks) + '\n' if url_checks else '')
    with open(filtered_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered) + '\n' if filtered else '')

    with open(dead_file, 'a', encoding='utf-8') as f:
        if dead:
            f.write("\n# === Явный мусор + мёртвые ===\n")
            f.write("\n".join(dead) + "\n")

    print(f"✅ Factory (только протоколы): {len(factory)}")
    print(f"🔗 Url_checks (Clash-правила и списки ссылок): {len(url_checks)}")
    print(f"🗑 Filtered: {len(filtered)}")
    print(f"💀 В бункер: {len(dead)}")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
