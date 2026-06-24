import asyncio
import aiohttp
import os
import re

BATCH_SIZE = 20000   # Увеличил до 20 тысяч, как ты хотел (можно 25000 или 30000)

# === СИЛЬНЫЕ ФИЛЬТРЫ ===
BAD_EXT = ['.lua', '.luau', '.apk', '.exe', '.zip', '.rar', '.tar', '.pdf', '.mp4', '.mp3']
BAD_KW = ['apple.com', 'releases', 'hiddify', 'karing', 'pywarp', 'docker', 'facebook', 'music', 'book', 'quote', 'steam', 'readme', 'youtube', 'boosty', 't.me/proxy', 'mtproto']

async def deep_check(session, url: str):
    try:
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
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

async def main():
    input_file = 'urls/source_urls.txt'
    chunks_dir = 'urls/urls'

    os.makedirs(chunks_dir, exist_ok=True)

    if not os.path.exists(input_file):
        print("❌ source_urls.txt не найден")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip().startswith(('http://', 'https://'))]

    print(f"🔍 Всего ссылок: {len(urls)}")
    print(f"📦 Разбиваю на чанки по {BATCH_SIZE} ссылок...\n")

    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        chunk_file = f"{chunks_dir}/chunk_{batch_num:03d}.txt"
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(batch) + '\n')
        
        print(f"   ✅ Сохранён {chunk_file} ({len(batch)} ссылок)")

    open(input_file, 'w').close()
    print("\n🧹 source_urls.txt очищен")
    print(f"🎉 Чанки сохранены в папке urls/urls/")

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
