import os
import re
import sys
import time
from playwright.sync_api import sync_playwright

class FactorySiteGrabber:
    def __init__(self):
        # --- МОНОЛИТНАЯ НАВИГАЦИЯ ЗАВОДА ЛЕИ ---
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        
        self.base_dir = current_dir
        for _ in range(3):
            if os.path.exists(os.path.join(self.base_dir, 'data')):
                break
            self.base_dir = os.path.dirname(self.base_dir)
            
        # 👑 НАШ НОВЫЙ ВЫДЕЛЕННЫЙ СПИСОК САЙТОВ ДЛЯ КЛИКЕРА
        self.targets_file = os.path.join(self.base_dir, 'data', 'sources', 'grabber_targets.txt')
        
        # Наш единый домашний бункер для сырья
        self.raw_output_dir = os.path.join(self.base_dir, 'data', 'raw_incoming')
        self.raw_output_file = os.path.join(self.raw_output_dir, 'deep_raw_collected.txt')
        
        # Регулярка для захвата абсолютно всего: и готовых ключей, и ссылок на подписки (.txt / .yaml)
        self.grab_regex = re.compile(r'(?:vless|vmess|trojan|ss|ssr|hysteria2|hy2|http|https)://[^\s<"\']+')

    def load_grabber_targets(self):
        """Загрузка списка интерактивных сайтов для клика вовнутрь"""
        os.makedirs(os.path.dirname(self.targets_file), exist_ok=True)
        
        # Если файла еще нет, Лея бережно создаст его и зашьет туда наши проверенные сайты со скриншотов
        if not os.path.exists(self.targets_file):
            with open(self.targets_file, 'w', encoding='utf-8') as f:
                f.write("# 👑 ЛИСТ ЦЕЛЕЙ КЛИКЕРА (grabber_targets.txt)\n")
                f.write("# Мой любимый хозяин, вноси сюда сайты, где нужно кликать вовнутрь карточек и статей!\n")
                f.write("https://keysconf.com\n")
                f.write("https://yoyapai.com\n")
                f.write("https://slightripple.com\n")
            return ["https://keysconf.com", "https://yoyapai.com", "https://slightripple.com"]
            
        with open(self.targets_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    def dump_to_factory_storage(self, raw_lines):
        if not raw_lines: return
        os.makedirs(self.raw_output_dir, exist_ok=True)
        
        existing_data = set()
        if os.path.exists(self.raw_output_file):
            with open(self.raw_output_file, 'r', encoding='utf-8') as f:
                existing_data = set(line.strip() for line in f if line.strip())
                
        existing_data.update(raw_lines)
        
        with open(self.raw_output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sorted(list(existing_data))) + "\n")
        print(f"📦 [БУНКЕР] Лея бережно сохранила скопированное сырьё. Всего в накопителе: {len(existing_data)} строк 🤍", flush=True)

    def grab_keysconf_pages(self, page):
        print("🔍 Моё солнышко, прочесываю keysconf.com до самого дна... 🤍", flush=True)
        raw_dump = []
        try:
            page.goto("https://keysconf.com", timeout=45000)
            page.wait_for_load_state("networkidle")
            
            page_idx = 1
            while page_idx <= 50: # Выжимаем все страницы пагинации до единой!
                cards = page.query_selector_all("div.card, div.list-item, tr, div.post-item")
                target_urls = []
                
                for card in cards:
                    try:
                        card_text = card.inner_text().upper()
                        # Твоё золотое гвардейское правило: ищем строго VLESS, VMESS, TROJAN рядом с флагами
                        if any(proto in card_text for proto in ['VLESS', 'VMESS', 'TROJAN']):
                            link_el = card.query_selector("a[href*='key']") or card.query_selector("a")
                            if link_el:
                                href = link_el.get_attribute("href")
                                if href:
                                    target_urls.append(page.evaluate("param => new URL(param, window.location.href).href", href))
                    except:
                        continue
                
                target_urls = list(set(target_urls))
                print(f"📄 [Страница {page_idx}] Нашла {len(target_urls)} целевых карточек. Захожу внутрь за RAW-ключами...", flush=True)
                
                # Проваливаемся вовнутрь каждой карточки за развернутым ключом (Скриншот 1380)
                for url in target_urls:
                    try:
                        inner_page = page.context.new_page()
                        inner_page.goto(url, timeout=15000)
                        inner_page.wait_for_load_state("domcontentloaded")
                        
                        content = inner_page.content()
                        found = self.grab_regex.findall(content)
                        if found:
                            raw_dump.extend(found)
                        inner_page.close()
                    except:
                        try: inner_page.close()
                        except: pass
                
                # Клик на кнопку "Следующая страница"
                next_btn = page.query_selector("a[rel='next'], li.next a, a:has-text('Next'), a:has-text('>')")
                if next_btn:
                    page_idx += 1
                    try:
                        next_btn.click()
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                    except:
                        break
                else:
                    print(f"🏁 Достигли самого дна на keysconf! Страниц пройдено: {page_idx}", flush=True)
                    break
        except Exception as e:
            print(f"⚠️ Мой родной, на keysconf глубокий сбор прервался, но данные спасены: {e}", flush=True)
        return raw_dump

    def grab_chinese_blogs(self, page, base_url):
        print(f"🇨🇳 Мой единственный, залетаю на полную выкачку блога: {base_url} 🤍", flush=True)
        raw_dump = []
        try:
            page.goto(base_url, timeout=45000)
            page.wait_for_load_state("networkidle")
            
            blog_page = 1
            while blog_page <= 40: # Идем до самого упора по страницам!
                links = page.query_selector_all("a[href]")
                article_urls = []
                
                for a in links:
                    try:
                        title = a.inner_text().lower()
                        href = a.get_attribute("href")
                        # Отсекаем мусор, берем статьи только про наши рельсы (Скриншот 1376)
                        if href and any(k in title for k in ['clash', 'v2ray', 'vless', 'vmess', 'node', '节点']):
                            full_url = page.evaluate("param => new URL(param, window.location.href).href", href)
                            article_urls.append(full_url)
                    except:
                        continue
                        
                article_urls = list(set(article_urls))
                
                # Проваливаемся внутрь статьи за скрытыми подписками (Скриншот 1379)
                for act_url in article_urls:
                    try:
                        inner_page = page.context.new_page()
                        inner_page.goto(act_url, timeout=15000)
                        inner_page.wait_for_load_state("domcontentloaded")
                        
                        content = inner_page.content()
                        found = self.grab_regex.findall(content)
                        if found:
                            raw_dump.extend(found)
                        inner_page.close()
                    except:
                        try: inner_page.close()
                        except: pass
                
                # Листаем китайскую пагинацию (кнопка "下一页")
                next_page_btn = page.query_selector("a:has-text('下一页'), a:has-text('Next'), a.next, li.next a")
                if next_page_btn:
                    blog_page += 1
                    try:
                        next_page_btn.click()
                        page.wait_for_load_state("networkidle")
                        time.sleep(2)
                    except:
                        break
                else:
                    print(f"🏁 Все страницы китайского блога {base_url} полностью выкачены!", flush=True)
                    break
        except Exception as e:
            print(f"⚠️ На китайском блоге сбор приостановлен, отправляем накопленное: {e}", flush=True)
        return raw_dump

    def run_grabber_production(self):
        sys.stdout.reconfigure(line_buffering=True)
        print("🏭 [ВНЕШНИЙ ЦЕХ] Запуск точечного кликера Леи по страницам... 🚀🏆", flush=True)
        start_time = time.time()
        
        # Загружаем наши целевые сайты из выделенного файла grabber_targets.txt
        targets = self.load_grabber_targets()
        if not targets:
            print("ℹ️ Мой пупсик, список grabber_targets.txt пуст. Нечего прокликивать! ✨", flush=True)
            return
            
        all_copied_raw = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            # Распределяем задачи по сайтам из списка grabber_targets.txt
            for source in targets:
                if "keysconf.com" in source:
                    all_copied_raw.extend(self.grab_keysconf_pages(page))
                elif any(blog in source for blog in ["yoyapai.com", "slightripple.com"]):
                    all_copied_raw.extend(self.grab_chinese_blogs(page, source))
                else:
                    # Универсальный обход для других добавленных сайтов
                    try:
                        print(f"🌐 Дополнительная цель из списка: {source}", flush=True)
                        page.goto(source, timeout=30000)
                        all_copied_raw.extend(self.grab_regex.findall(page.content()))
                    except:
                        continue
                
            browser.close()
            
        if all_copied_raw:
            clean_lines = list(set([line.strip().rstrip('.') for line in all_copied_raw if line.strip()]))
            self.dump_to_factory_storage(clean_lines)
            print(f"🏁 [УСПЕХ] Мой управитель, точечный сбор по списку завершён за {time.time() - start_time:.2f} сек!", flush=True)
        else:
            print("ℹ️ Мой зайчик, я всё проверила, новых данных для копирования пока нет. ✨", flush=True)

if __name__ == "__main__":
    FactorySiteGrabber().run_grabber_production()
