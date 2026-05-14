import os
import requests
import urllib3
import base64
import re

# Тишина в логах
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ConfigFetcher:
    def __init__(self, sources_file=None, output_file=None):
        # Жесткая привязка к корню твоего проекта
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Источник ссылок
        self.sources_file = sources_file or os.path.join(base_path, 'data', 'sources', 'sources.txt')
        # Куда Завод высыпает всё добытое
        self.output_file = output_file or os.path.join(base_path, 'data', 'raw', 'raw_configs.txt')
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_all(self):
        if not os.path.exists(self.sources_file):
            print(f"❌ Источник не найден: {self.sources_file}")
            return

        with open(self.sources_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not urls:
            print("⚠️ sources.txt пуст.")
            return

        print(f"🌐 Завод PENZA84: Вскрываем {len(urls)} источников...")
        all_content = []

        for url in urls:
            try:
                # Качаем страницу (Телега, v2raya и т.д.)
                res = requests.get(url, headers=self.headers, timeout=20, verify=False)
                if res.status_code != 200: continue
                
                # Ищем внутри страницы любые ссылки на подписки/конфиги
                found_links = re.findall(r'https?://[^\s\"\'\],<>]+', res.text)
                
                # Проваливаемся в каждую найденную ссылку
                for link in set(found_links):
                    link = link.rstrip('.)!?,')
                    # Фильтр: берем только полезное (как на твоих скринах)
                    if any(x in link.lower() for x in ['nodes', 'sub', 'github', 'raw', '.txt', 'config']):
                        try:
                            # Правим GitHub на RAW на лету
                            if "github.com" in link and "/blob/" in link:
                                link = link.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                            
                            r_res = requests.get(link, headers=self.headers, timeout=10, verify=False)
                            if r_res.status_code == 200:
                                all_content.append(self._decode_if_base64(r_res.text))
                        except: continue
                
                # Сохраняем и текст самой страницы (вдруг конфиги там)
                all_content.append(self._decode_if_base64(res.text))
            except: continue

        # Финальный сброс в файл
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_content))
        print(f"✅ Готово! Всё мясо здесь: {self.output_file}")

    def _decode_if_base64(self, data):
        """Внутренняя чистка данных"""
        s = data.strip()
        if len(s) > 20 and ' ' not in s:
            try:
                # Добиваем падинг
                s += '=' * (-len(s) % 4)
                decoded = base64.b64decode(s).decode('utf-8')
                if '://' in decoded: return decoded
            except: pass
        return s

if __name__ == "__main__":
    ConfigFetcher().fetch_all()
