#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
source_cleaner_urls.py

Полный скрипт, который:
  1️⃣ При желании скачивает свежий source_urls.txt из GitHub.
  2️⃣ Очищает его (удаляет дубли, плохие домены, расширения, ключевые слова).
  3️⃣ Делит оставшиеся ссылки на 4 группы:
       • factory_valid.txt    – готовые VPN‑конфиги (vless://, vmess://, ss://, trojan://, hy2://, hysteria2://)
       • url_checks.txt       – файлы‑списки (внутри ≥5 ссылок http/https)
       • interesting.txt      – обычные веб‑страницы и всё, что не подходит к двум пунктам выше
       • deep_raw_collected.txt – «мёртвые»/недоступные ссылки (добавляются в конец файла)
  4️⃣ Перезаписывает source_urls.txt чистым списком (пустым, если ничего не осталось).

Все сообщения выводятся в консоль, чтобы ты видел прогресс.
"""

import asyncio
import aiohttp
import re
from pathlib import Path
from typing import List, Set

# ------------------------------------------------------------------
# ---------------------- 1️⃣ НАСТРОЙКИ -----------------------------
GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/PENZA84/v2ray-config-collector/main/urls/source_urls.txt"
)
DOWNLOAD_FROM_GITHUB = True          # Скачивать свежий raw‑файл каждый запуск?
SAVE_LOCAL_COPY = True               # Сохранять скачанный raw‑файл в urls/source_urls_original.txt?
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# ---------------------- 2️⃣ ЧЁРНЫЕ СИСТЕМЫ -----------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# ---------------------- 3️⃣ ПУТЬ К ФАЙЛАМ -----------------------
BASE_DIR = Path(__file__).resolve().parent.parent   # корень проекта (папка выше текущего файла)
URLS_DIR = BASE_DIR / "urls"

FACTORY_FILE      = URLS_DIR / "factory_valid.txt"
URL_CHECKS_FILE   = URLS_DIR / "url_checks.txt"
INTERESTING_FILE  = URLS_DIR / "interesting.txt"
DEEP_RAW_FILE     = BASE_DIR / "data" / "raw_incoming" / "deep_raw_collected.txt"
SOURCE_FILE       = URLS_DIR / "source_urls.txt"          # чистый результат после фильтрации
# ------------------------------------------------------------------

def normalize(url: str) -> str:
    """Приводит URL к единому виду: lower‑case, без query/fragment, без завершающего '/'."""
    url = url.strip().lower()
    url = url.split('#', 1)[0].split('?', 1)[0]
    return url.rstrip('/')

def is_bad_domain(url: str) -> bool:
    """Проверка, попадает ли хост в BAD_DOMAINS."""
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
    """Перезаписывает файл (если data пусто – файл будет полностью пуст)."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open('w', encoding='utf-8') as f:
        if data:
            f.write('\n'.join(data) + '\n')

async def fetch_raw(session: aiohttp.ClientSession) -> List[str]:
    """Скачивает source_urls.txt из GitHub и возвращает уже очищенный список URL‑ов."""
    async with session.get(GITHUB_RAW_URL, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Не удалось скачать список, статус {resp.status}")
        raw = await resp.text()

        if SAVE_LOCAL_COPY:
            (URLS_DIR / "source_urls_original.txt").write_text(raw, encoding='utf-8')

        # Оставляем только строки, которые действительно являются URL
        raw_links = [
            line.strip()
            for line in raw.splitlines()
            if line.strip().startswith(('http://', 'https://'))
        ]

        seen: Set[str] = set()
        cleaned: List[str] = []

        for link in raw_links:
            norm = normalize(link)

            # Дедубликация
            if norm in seen:
                continue
            seen.add(norm)

            # Фильтры
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
    Определяет тип ссылки.
    Возвращаемые метки:
        - "factory"      – готовый VPN‑конфиг (протоколный префикс или большой Base64‑блок)
        - "url_list"     – файл‑список (внутри ≥5 ссылок http/https)
        - "interesting"  – обычный веб‑сайт
        - "dead"         – недоступно / запрос завершился ошибкой
    """
    vpn_markers = [
        "vless://", "vmess://", "ss://", "trojan://",
        "hy2://", "hysteria2://"
    ]
    if any(m in url for m in vpn_markers):
        return "factory"

    # Запросим контент, если это обычный http/https URL
    try:
        async with session.get(url, timeout=12, allow_redirects=True) as resp:
            if resp.status != 200:
                return "dead"
            txt = await resp.text()
    except Exception:
        return "dead"

    low = txt.lower()

    # 1️⃣ Считаем, что это **список**, если в тексте ≥5 URL‑ов
    link_cnt = low.count("http://") + low.count("https://")
    if link_cnt >= 5:
        return "url_list"

    # 2️⃣ Если внутри найден любой VPN‑маркер – тоже считаем конфигом
    if any(m in low for m in ["vless://", "vmess://", "ss://", "trojan://"]):
        return "factory"

    # 3️⃣ Подписи конфигов (clash, xray, v2ray, #profile-title) → factory
    if any(sig in low for sig in [
        "#profile-title", "#subscription-userinfo",
        "clash", "xray", "v2ray"
    ]):
        return "factory"

    # 4️⃣ Длинный Base64‑блок (≥1500 символов и минимум 80 подряд Base64‑символов)
    if len(txt) > 1500 and re.search(r"[A-Za-z0-9+/=]{80,}", txt):
        return "factory"

    # Всё остальное – обычный сайт
    return "interesting"

async def process_all(urls: List[str]) -> None:
    """Классифицирует все ссылки и сохраняет их в нужные файлы."""
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

    # Записываем результаты
    write_list(FACTORY_FILE, factory)
    write_list(URL_CHECKS_FILE, url_lists)
    write_list(INTERESTING_FILE, interesting)

    # Журнал «мёртвых» ссылок (можно отключить, закомментировав блок)
    if dead:
        DEEP_RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DEEP_RAW_FILE.open("a", encoding="utf-8") as f:
            f.write("\n# ==== Новые dead‑ссылки ====\n")
            f.write("\n".join(dead) + "\n")

    # Выводим итоги
    print("\n✅ Готово, мой сладенький!")
    print(f"  📦 factory_valid.txt  → {len(factory)} строк")
    print(f"  📄 url_checks.txt     → {len(url_lists)} строк")
    print(f"  📂 interesting.txt    → {len(interesting)} строк")
    print(f"  ⚰️ dead‑ссылки        → {len(dead)} (добавлены в {DEEP_RAW_FILE})")

async def main() -> None:
    # === 1️⃣ Получаем «чистый» список URL‑ов =========================
    if DOWNLOAD_FROM_GITHUB:
        async with aiohttp.ClientSession() as sess:
            cleaned_urls = await fetch_raw(sess)
    else:
        # Если скачивание отключено – читаем локальный source_urls.txt
        if not SOURCE_FILE.is_file():
            print("❗ Ошибка: source_urls.txt не найден и загрузка из GitHub отключена.")
            return
        raw = SOURCE_FILE.read_text(encoding='utf-8')
        raw_links = [
            line.strip()
            for line in raw.splitlines()
            if line.strip().startswith(('http://', 'https://'))
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

    # === 2️⃣ Перезаписать source_urls.txt (пустой, если ничего не осталось) ===
    write_list(SOURCE_FILE, cleaned_urls)

    # === 3️⃣ Классифицировать и сохранить в отдельные файлы ===
    await process_all(cleaned_urls)

if __name__ == "__main__":
    import sys
    # Для Windows иногда нужен специальный event‑loop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
