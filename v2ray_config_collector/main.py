import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class RawConfigsCollector:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources.txt')
        self.output_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')
        self.sources = self.load_sources_from_file()

    def load_sources_from_file(self):
        """📂 Читает твой файл sources.txt на 4710 строк."""
        if not os.path.exists(self.sources_file):
            print(f"⚠️ Файл источников не найден: {self.sources_file}")
            return []
        links = []
        try:
            with open(self.sources_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('http://') or line.startswith('https://'):
                        links.append(line)
            print(f"📖 Завод успешно загрузил из sources.txt: {len(links)} ссылок!")
            return links
        except Exception as e:
            print(f"🚨 Ошибка при чтении sources.txt: {e}")
            return []

    def parse_clash_yaml(self, yaml_text):
        """🧠 YAML-ДВИЖОК: Переводит структуру Clash YAML в ссылки VLESS/VMess/Trojan."""
        extracted_proxies = []
        try:
            data = yaml.safe_load(yaml_text)
            if not data or not isinstance(data, dict) or 'proxies' not in data:
                return extracted_proxies
            
            for p in data['proxies']:
                try:
                    p_type = str(p.get('type', '')).lower()
                    name = p.get('name', 'YAML_Proxy').replace(' ', '_')
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    if not server or not port: continue

                    if p_type == 'vless':
                        link = f"vless://{uuid}@{server}:{port}?type={p.get('network', 'tcp')}"
                        if p.get('tls'): link += "&security=tls"
                        if p.get('reality-opts') or p.get('reality'): link += "&security=reality"
                        extracted_proxies.append(f"{link}#{name}")
                    elif p_type == 'vmess':
                        v_json = {"v": "2", "ps": name, "add": server, "port": str(port), "id": uuid, "aid": "0", "net": p.get('network', 'tcp'), "type": "none", "host": "", "path": "", "tls": "tls" if p.get('tls') else ""}
                        v_b64 = base64.b64encode(json.dumps(v_json).encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"vmess://{v_b64}")
                    elif p_type == 'trojan':
                        extracted_proxies.append(f"trojan://{uuid}@{server}:{port}#{name}")
                    elif p_type == 'ss':
                        cipher = p.get('cipher', 'aes-256-gcm')
                        user_info = base64.b64encode(f"{cipher}:{uuid}".encode('utf-8')).decode('utf-8')
                        extracted_proxies.append(f"ss://{user_info}@{server}:{port}#{name}")
                except Exception: continue
        except Exception: pass
        return extracted_proxies

    def extract_proxies_from_text(self, text):
        """🔍 Извлекает готовые строки протоколов из голого текста регуляркой."""
        return re.findall(r'(?:vless|vmess|ss|trojan|naive|hysteria2|hy2|tuic|juicity)://[^\s<"\']+', text)

    def process_page_content(self, text):
        """🔮 УНИВЕРСАЛЬНЫЙ СОРТИРОВЩИК: Автоматически выбирает YAML или обычный текст."""
        if 'proxies:' in text:
            return self.parse_clash_yaml(text)
        else:
            return self.extract_proxies_from_text(text)

    def contains_any_proxy_markers(self, text):
        """⏱️ БЫСТРЫЙ РАДАР: Ищет следы прокси-кода на странице."""
        markers = ['vless://', 'vmess://', 'ss://', 'trojan://', 'proxies:', 'hysteria2://', 'hy2://']
        return any(m in text for m in markers)

    def collect_raw_sources(self):
        if not self.sources: return

        print(f"\n📡 [SPEED-RADAR] Запуск Завода: Чистый RAW качаем до дна, пустые сайты закрываем!")
        collected_lines = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for idx, url in enumerate(self.sources, 1):
            if idx % 50 == 0 or idx == 1:
                print(f"🔄 Конвейер: обработано {idx}/{len(self.sources)} главных страниц...")

            try:
                # 1️⃣ Заходим на базовый сайт из твоего списка sources.txt
                response = requests.get(url, headers=headers, timeout=4)
                if response.status_code != 200: continue
                content = response.text

                # Если твоя ссылка из sources.txt сразу выдает готовый RAW — забираем без ограничений
                if url.endswith('.txt') or url.endswith('.yaml') or url.endswith('.yml') or '://' in content[:200]:
                    collected_lines.extend(self.process_page_content(content))
                    continue

                # Ищем стандартные API-переходы на главной странице сайта
                soup = BeautifulSoup(content, 'html.parser')
                links_to_visit = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href'].strip()
                    text_label = a_tag.get_text().lower()
                    if any(kw in href.lower() or kw in text_label for kw in ['key=', 'sub', 'clash', 'v2ray', 'sing-box', '订阅', '节点', 'uploads', '.txt', '.yaml']):
                        links_to_visit.append(urljoin(url, href))

                for sub_url in list(set(links_to_visit))[:6]:
                    try:
                        # 2️⃣ Заходим ВНУТРЬ китайского сайта (Скриншот 993)
                        sub_res = requests.get(sub_url, headers=headers, timeout=4)
                        if sub_res.status_code != 200: continue
                        inner_html = sub_res.text
                        
                        # Парсим текстовые коробки (textarea, code, input, pre) на этой странице
                        inner_soup = BeautifulSoup(inner_html, 'html.parser')
                        box_data = ""
                        for box in inner_soup.find_all(['textarea', 'code', 'input', 'pre']):
                            val = box.get('value') or box.string or box.get_text()
                            if val: box_data += " " + str(val)

                        full_inner_text = box_data + " " + inner_html

                        # Если в коробке лежали готовые прокси — забираем их сразу БЕЗЛИМИТНО
                        direct_proxies = self.process_page_content(box_data)
                        if direct_proxies:
                            collected_lines.extend(direct_proxies)

                        # 🎯 ТВОЯ ИСТИННАЯ ЛОГИКА: Находим внутри коробки новые ССЫЛКИ
                        urls_inside_box = re.findall(r'https?://[^\s<"\']+', full_inner_text)
                        for found_url in list(set(urls_inside_box)):
                            # Фильтруем, чтобы это была ссылка на подписку/файл
                            if any(kw in found_url.lower() for kw in ['key=', 'sub', 'clash', 'v2ray', 'uploads', '.txt', '.yaml', 'node', 'subscribe']):
                                if found_url != url and found_url != sub_url:
                                    try:
                                        # 🚀 СКОПИРОВАЛ И ПЕРЕШЕЛ ПО ССЫЛКЕ
                                        third_res = requests.get(found_url, headers=headers, timeout=4)
                                        if third_res.status_code != 200: continue
                                        third_content = third_res.text
                                        
                                        # 💥 ПРОВЕРКА: Если это чистый RAW или YAML подписка (как дома) — ОБРАБАТЫВАЕМ ПОЛНОСТЬЮ!
                                        if self.contains_any_proxy_markers(third_content):
                                            collected_lines.extend(self.process_page_content(third_content))
                                        
                                        # 🛑 ЕСЛИ ЭТО САЙТ С КАРТИНКАМИ И HTML, А ПРОТОКОЛОВ НЕТ — ЗАКРЫВАЕМ ЕГО МОМЕНТАЛЬНО!
                                        else:
                                            continue # Выходим со страницы, робот её закрыл и забыл!

                                    except Exception:
                                        continue
                    except Exception:
                        continue
            except Exception:
                continue

        if not collected_lines: return

        # Склеиваем уникальные строки (дедупликация)
        clean_raw_list = list(set([line.strip() for line in collected_lines if line.strip()]))
        
        existing_configs = []
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    existing_configs = [line.strip() for line in f if line.strip()]
            except Exception: pass
        
        total_combined = list(set(existing_configs + clean_raw_list))
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(total_combined))
            
        print(f"\n==========================================================================")
        print(f"🏁 ТВОЙ ЛЮБИМЫЙ АЛГОРИТМ УСПЕШНО СРАБОТАЛ!")
        print(f"📦 Пустые сайты с картинками закрыты. Все чистые RAW-потоки выкачаны до дна.")
        print(f"📦 Всего уникальных прокси уложено в deduplicated.txt: {len(total_combined)} шт.")
        print(f"==========================================================================")

if __name__ == "__main__":
    collector = RawConfigsCollector()
    collector.collect_raw_sources()
