import asyncio
import aiohttp
import os
import re
import argparse

print("=== clicker.py [Максимальная Генерация & Резчик Хвостов] запущен ===")

# Статический мусор (картинки и стили) по-прежнему пропускаем, чтобы не забивать память
SKIP_EXTENSIONS = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.pdf']

async def fetch_and_extract(session, target_url: str):
    target_url_lower = target_url.lower()

    if target_url_lower.endswith(('.yml', '.yaml')) or '.ru' in target_url_lower:
        return []
    if any(target_url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
        return []

    try:
        async with session.get(target_url, timeout=15, allow_redirects=True) as resp:
            if resp.status != 200:
                return []

            text = await resp.text(errors='ignore')
            text_lower = text.lower()
            
            is_html = 'text/html' in resp.headers.get('Content-Type', '').lower() or any(tag in text_lower for tag in ['<!doctype html', '<html', '<body'])

            # =====================================================================
            # 🔥 ПРОВЕРКА НА ПРЯМОЙ КОД / ПОДПИСКУ (БАЗА 64 И ПРОТОКОЛЫ)
            # =====================================================================
            is_factory_source = False
            if any(p in text_lower for p in ['vless://', 'vmess://', 'ss://', 'trojan://', 'hy2://', 'hysteria2://', 'socks://', 'socks5://']):
                is_factory_source = True
            elif any(sign in text_lower for sign in ['#profile-title', '#subscription-userinfo', 'clash', 'xray', 'v2ray']):
                is_factory_source = True
            elif not is_html and re.search(r'[A-Za-z0-9+/=]{60,}', text):
                is_factory_source = True

            if is_factory_source:
                print(f" ✨ Найдена прямая подписка/код: {target_url}")
                return [target_url]

            # =====================================================================
            # 🔗 МАКСИМАЛЬНАЯ ГЕНЕРАЦИЯ С ЮВЕЛИРНОЙ ОЧИСТКОЙ ДЛЯ ТЕБЯ
            # =====================================================================
            found_urls = re.findall(r'https?://[^\s"\'>]+', text)
            clean_extracted = set()

            for raw_url in found_urls:
                url = raw_url
                
                # 🔥 Намертво срезаем HTML-теги, JSON-экранирование, кавычки и слэши из логов
                for junk in ['&quot;', '\\u003c', '</a', '\\u003e', '\\', '"', "'", '<', '>', '}', '{']:
                    if junk in url:
                        url = url.split(junk)[0]
                
                # Подчищаем правый край от знаков препинания и остаточных символов
                url = url.rstrip('.,;)精神\\/')
                url_lower = url.lower()

                # Проверяем длину и базовые фильтры
                if not url or len(url) < 10:
                    continue
                if '.ru' in url_lower or url_lower.endswith(('.yml', '.yaml')):
                    continue
                if any(url_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                    continue
                
                # Пропускаем только пустую главную страницу гитхаба и схемы
                if url_lower in ['https://github.com', 'https://github.com/', 'https://schema.org']:
                    continue

                clean_extracted.add(url)

            return list(clean_extracted)

    except Exception as e:
        print(f" ❌ Ошибка клика по {target_url}: {e}")
        return []

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=str, default='clicker/profiles.txt')
    parser.add_argument('--output', type=str, default='clicker/extracted_urls.txt')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ Файл {args.input} не найден.")
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        source_urls = [line.strip() for line in f if line.strip()]

    if not source_urls:
        return
    
    print(f" Начинаю обход {len(source_urls)} адресов...")
    all_extracted_links = set()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_and_extract(session, url) for url in source_urls]
        results = await asyncio.gather(*tasks)

        for links_list in results:
            for link in links_list:
                all_extracted_links.add(link)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        for link in sorted(all_extracted_links):
            f.write(f"{link}\n")

    print(f" 💾 Готово! В базу кликера сохранено уникальных адресов: {len(all_extracted_links)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
