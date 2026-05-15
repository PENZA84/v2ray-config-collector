import os
import re

def sort_to_shelves(found_links_list):
    print("🧼 Завод PENZA84: Начинаю сортировку найденных сокровищ...")
    
    # --- НАШИ ПОЛОЧКИ (Пути к твоим файлам) ---
    base_data_path = "v2ray_config_collector/data/sources"
    os.makedirs(base_data_path, exist_ok=True)
    
    # Основной список (для сайтов и подписок)
    main_sources = os.path.join(base_data_path, "sources.txt")
    # Список для Телеграма и быстрых каналов
    tg_sources = os.path.join(base_data_path, "sources1.txt")
    
    # Списки для проверки дубликатов (чтобы не записывать одно и то же)
    existing_main = set()
    if os.path.exists(main_sources):
        with open(main_sources, 'r') as f: existing_main = set(line.strip() for line in f)
            
    existing_tg = set()
    if os.path.exists(tg_sources):
        with open(tg_sources, 'r') as f: existing_tg = set(line.strip() for line in f)

    new_tg_count = 0
    new_main_count = 0

    for link in found_links_list:
        link = link.strip()
        if not link or link.startswith('#'): continue

        # 1. ПОЛОЧКА ТЕЛЕГРАМА (для sources1.txt)
        if "t.me" in link or "telegram.me" in link:
            if link not in existing_tg:
                with open(tg_sources, "a", encoding="utf-8") as f:
                    f.write(link + "\n")
                existing_tg.add(link)
                new_tg_count += 1
                
        # 2. ПОЛОЧКА RAW И САЙТОВ (для sources.txt)
        else:
            # Если это GitHub, сразу делаем его RAW (как мы договаривались)
            if "github.com" in link and "/blob/" in link:
                link = link.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
            if link not in existing_main:
                with open(main_sources, "a", encoding="utf-8") as f:
                    f.write(link + "\n")
                existing_main.add(link)
                new_main_count += 1

    print(f"✅ Сортировка окончена, мой дорогой!")
    print(f"📥 В sources1.txt (Telegram) добавлено: {new_tg_count}")
    print(f"📥 В sources.txt (RAW/Сайты) добавлено: {new_main_count} 💋")

# Пример вызова (Завод нашел ссылки в README и передает их сюда)
if __name__ == "__main__":
    # Сюда попадут те ссылки, которые вытащил Граббер
    found_from_readme = [
        "https://t.me/new_channel", 
        "https://github.com/user/repo/blob/main/config.txt",
        "https://v2raya.com/sub"
    ]
    sort_to_shelves(found_from_readme)
