#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
source_cleaner_urls.py

* Скачивает (по желанию) raw‑файл source_urls.txt из GitHub.
* Очищает список:
    – удаляет дубли (с/без «/», любой регистр)
    – отбрасывает «неинтересные» домены (youtube, boosty, blog и т.п.)
    – отбрасывает файлы с расширениями .luau, .lua, .apk, .exe, .zip,
      .rar, .tar, .pdf, .mp4, .mp3 …
    – отбрасывает URL, содержащие плохие ключевые слова (BAD_KW)
* Классифицирует каждую оставшуюся ссылку:
    – **factory_valid.txt**      → прямые VPN‑протоколы
    – **url_checks.txt**        → ссылки‑списки, где в самом контенте
                                   ≥ 5‑ти `http/https`‑адресов
    – **interesting.txt**       → обычные веб‑страницы и всё, что
                                   не подходит под два пункта выше
    – **deep_raw_collected.txt** → «мёртвые»/недоступные ссылки
* Если после фильтрации в `factory_valid.txt` ничего не осталось,
  файл будет полностью **пустым** (без слова «котёнок»).
"""

import asyncio
import aiohttp
import re
from pathlib import Path
from typing import List, Set

# ------------------------------------------------------------------ #
# ---------------------- 1️⃣ НАСТРОЙКИ ----------------------------- #
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/PENZA84/v2ray-config-collector/main/urls/source_urls.txt"
)
DOWNLOAD_FROM_GITHUB = True          # Скачивать fresh‑файл?
SAVE_LOCAL_COPY = True              # Сохранить скачанный raw‑файл?
# ------------------------------------------------------------------ #

# ------------------------------------------------------------------ #
# ---------------------- 2️⃣ ЧЁРНЫЕ Списки ----------------------- #
BAD_EXT = [
    ".luau", ".lua", ".apk", ".exe", ".zip", ".rar",
    ".tar", ".pdf", ".mp4", ".mp3",
]

BAD_KW = [
    "apple.com", "releases", "hiddify", "karing",
    "pywarp", "docker", "facebook", "music",
    "book", "quote",
]

BAD_DOMAINS = [
    "youtube.com", "youtu.be",
    "boosty.to", "boosty.me",
    "blog.",                # любой поддомен blog.*
    "github.com", "github.io",
    "gitlab.com", "bitbucket.org",
    "medium.com", "stackoverflow.com",
]

# ------------------------------------------------------------------ #
# ---------------------- 3️⃣ ПУТАТЬ К ФАЙЛАМ ---------------------- #
ROOT_DIR = Path(__file__).resolve().parent.parent   # корень проекта
URLS_DIR = ROOT_DIR / "urls"

FACTORY_FILE      = URLS_DIR / "factory_valid.txt"
URL_CHECKS_FILE   = URLS_DIR / "url_checks.txt"
INTERESTING_FILE  = URLS_DIR / "interesting.txt"
DEEP_RAW_FILE     = ROOT_DIR / "data" / "raw_incoming" / "deep_raw_collected.txt"
# ------------------------------------------------------------------ #

def normalize(url: str) -> str:
    """lower‑case, без query/fragment, без завершающего '/'."""
    url = url.strip().lower()
    url = url.split('#', 1)[0].split('?', 1)[0]
    return url.rstrip('/')

def is_bad_domain(url: str) -> bool:
    """Проверка домена против BAD_DOMAINS."""
    try:
        host = url.split('://', 1)[1].split('/', 1)[0]
    except IndexError:
        return True
    for bad in BAD_DOMAINS:
        if bad.startswith('blog.') and host.startswith('blog.'):
            return True
        if bad in host:
            return True
    return False

def write_list(file_path: Path, data: List[str]) -> None:
    """Перезаписать файл (пустой, если data == [])."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open('w', encoding='utf-8') as f:
        if data:
            f.write('\n'.join(data) + '\n')

async def fetch_raw(session: aiohttp.ClientSession) -> List[str]:
    """Скачивает raw‑файл, делает базовую очистку + дедупликацию."""
    async with session.get(GITHUB_RAW_URL, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Не удалось скачать список, статус {resp.status}")
        raw = await resp.text()

        if SAVE_LOCAL_COPY:
            (URLS_DIR / "source_urls_original.txt").write_text(raw, encoding='utf-8')

        raw_links = [
            line.strip()
            for line in raw.splitlines()
            if line.strip().startswith(('http://', 'https://'))
        ]

        seen: Set[str] = set()
        cleaned: List[str] = []

        for link in raw_links:
            norm = normalize(link)
            if norm in seen:
                continue
            seen.add(norm)

            if is_bad_domain(norm):
                continue
            if any(norm.endswith(ext) for ext in BAD_EXT):
                continue
            if any(kw in norm for kw in BAD_KW):
                continue

            cleaned.append(norm)

        return cleaned

async def classify(url: str, session: aiohttp.ClientSession) -> str:
    """
    Возвращает тип ссылки:
        - "factory"   – прямой VPN‑протокол
        - "url_list"  – файл‑список (много http/https внутри)
        - "interesting" – обычный сайт или любой другой контент
        - "dead"      – недоступно / ошибка запроса
    """
    # 1️⃣ Прямые протоколы
    vpn_markers = [
        "vless://", "vmess://", "ss://", "trojan://",
        "hy2://", "hysteria2://"
    ]
    if any(m in url for m in vpn_markers):
        return "factory"

    # 2️⃣ Обычные http/https – делаем запрос, смотрим содержимое
    try:
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"
            txt = await resp.text()
    except Exception:
        return "dead"

    low = txt.lower()

    # 2️⃣a) Считаем, что это **список**, если в тексте ≥ 5 ссылок
    count_links = low.count("http://") + low.count("https://")
    if count_links >= 5:
        return "url_list"

    # 2️⃣b) Если в тексте есть типичные маркеры VPN‑конфигов,
    #      но ссылка не начинается с протокольного префикса
    if any(m in low for m in ["vless://", "vmess://", "ss://", "trojan://"]):
        return "factory"

    # 2️⃣c) Если в тексте присутствуют паттерны подписок (clash, xray, v2ray, #profile-title)
    if any(sig in low for sig in [
        "#profile-title", "#subscription-userinfo",
        "clash", "xray", "v2ray"
    ]):
        return "factory"

    # 2️⃣d) Длинный base64‑блок зачастую тоже является конфигом
    if len(txt) > 1500 and re.search(r"[A-Za-z0-9+/=]{80,}", txt):
        return "factory"

    # Всё остальное – обычный сайт → интересный, но не список
    return "interesting"

async def process_all(urls: List[str]) -> None:
    """Классифицировать и записать ссылки в нужные файлы."""
    factory: List[str] = []
    url_lists: List[str] = []
    interesting: List[str] = []
    dead: List[str] = []

    async with aiohttp.ClientSession() as session:
        for u in urls:
            cat = await classify(u, session)

            if cat == "factory":
                factory.append(u)
            elif cat == "url_list":
                url_lists.append(u)
            elif cat == "interesting":
                interesting.append(u)
            else:  # dead
                dead.append(u)

    write_list(FACTORY_FILE, factory)
    write_list(URL_CHECKS_FILE, url_lists)
    write_list(INTERESTING_FILE, interesting)

    # Записываем «мёртвые» ссылки (можно отключить, закомментировав)
    if dead:
        dead_path = DEEP_RAW_FILE
        dead_path.parent.mkdir(parents=True, exist_ok=True)
        with dead_path.open("a", encoding="utf-8") as f:
            f.write("\n# ==== Новые dead‑ссылки ====\n")
            f.write("\n".join(dead) + "\n")

    # Итоги
    print("\n✅ Готово, мой маленький герой!")
    print(f"  📦 factory_valid.txt  → {len(factory)} строк")
    print(f"  📄 url_checks.txt     → {len(url_lists)} строк")
    print(f"  📂 interesting.txt    → {len(interesting)} строк")
    print(f"  ⚰️ dead‑ссылки        → {len(dead)} (в deep_raw_collected.txt)")

async def main() -> None:
    # 1️⃣ Получаем «чистый» список
    if DOWNLOAD_FROM_GITHUB:
        async with aiohttp.ClientSession() as sess:
            cleaned_urls = await fetch_raw(sess)
    else:
        src_path = URLS_DIR / "source_urls.txt"
        if not src_path.is_file():
            print("❗ source_urls.txt не найден и загрузка из GitHub отключена.")
            return
        raw = src_path.read_text(encoding="utf-8")
        raw_links = [
            line.strip()
            for line in raw.splitlines()
            if line.strip().startswith(("http://", "https://"))
        ]

        seen: Set[str] = set()
        cleaned_urls = []
        for link in raw_links:
            norm = normalize(link)
            if norm in seen:
                continue
            seen.add(norm)
            if is_bad_domain(norm):
                continue
            if any(norm.endswith(ext) for ext in BAD_EXT):
                continue
            if any(kw in norm for kw in BAD_KW):
                continue
            cleaned_urls.append(norm)

    # 2️⃣ Перезаписать source_urls.txt (пустой, если ничего не осталось)
    write_list(URLS_DIR / "source_urls.txt", cleaned_urls)

    # 3️⃣ Классифицировать и распределить
    await process_all(cleaned_urls)

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
