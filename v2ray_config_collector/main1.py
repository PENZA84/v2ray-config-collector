import os
import re
import requests
import yaml
import json
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class TelegramRawCollector:
    def __init__(self):
        # Определение базовых путей проекта
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sources_file = os.path.join(self.base_dir, 'data', 'sources', 'sources1.txt')
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.max_file_size_mb = 40
        
        # Список поддерживаемых протоколов (собраны в одном месте для надежности)
        self.protocols = [
            'naive+https', 'vless', 'vmess', 'ss', 'trojan', 'naive', 
            'hysteria2', 'hy2', 'tuic', 'juicity', 'socks5', 'socks4', 
            'socks', 'http', 'https', 'shadowtls', 'wireguard', 'wg', 
            'ssh', 'anytls', 'trusttunnel'
        ]
        
        # Компилируем регулярное выражение один раз для высокой скорости работы
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')
        
        # Загрузка источников
        self.sources = self.load_sources()

    def load_sources(self):
        """Загрузка ссылок на источники из файла источников"""
        if not os.path.exists(self.sources_file): 
            return []
        links = []
        with open(self.sources_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('http'): 
                    links.append(line)
        return links

    def process_content(self, text):
        """Поиск всех конфигураций прокси в тексте, включая сложные параметры"""
        return self.regex_pattern.findall(text)

    def split_and_save_file(self, prefix, base_name, lines):
        """Разбивка файлов по 40 МБ и сохранение с префиксом 'ТГ '"""
        if not lines: 
            return
        full_base_name = f"{prefix}{base_name}"
        
        # Очистка старых файлов перед записью новых
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f == f"{full_base_name}.txt" or re.match(r'^' + re.escape(full_base_name) + r'\s+\d+\.txt$', f):
                    try: 
                        os.remove(os.path.join(self.output_dir, f))
                    except: 
                        pass

        parts = []
        current_chunk = []
        current_size = 0
        max_bytes = self.max_file_size_mb * 1024 * 1024

        for line in lines:
            line_bytes = (line + "\n").encode('utf-8')
            if current_size + len(line_bytes) > max_bytes and current_chunk:
                parts.append(current_chunk)
                current_chunk = [line]
                current_size = len(line_bytes)
            else:
                current_chunk.append(line)
                current_size += len(line_bytes)
        if current_chunk:
            parts.append(current_chunk)

        # Запись чанков в файлы
        for idx, chunk_lines in enumerate(parts):
            if idx == 0:
                part_file = os.path.join(self.output_dir, f"{full_base_name}.txt")
            else:
                part_file = os.path.join(self.output_dir, f"{full_base_name} {idx}.txt")
            
            with open(part_file, 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines))

    def collect(self):
        """Основной метод сбора и фильтрации прокси-конфигов"""
        if not self.sources: 
            return
        collected = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }
        
        for url in self.sources:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code != 200: 
                    continue
                content = res.text
                
                # Если прямая ссылка на txt или контент сразу начинается с прокси
                if url.endswith('.txt') or '://' in content[:200]:
                    collected.extend(self.process_content(content))
                    continue
                
                # Проверка наличия любого из поддерживаемых протоколов в теле ответа
                if any(f"{proto}://" in content for proto in self.protocols):
                    collected.extend(self.process_content(content))
            except: 
                continue

        if collected:
            # Очистка строк от пробелов и удаление дубликатов
            clean = list(set([l.strip() for l in collected if l.strip() and '://' in l]))
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Сохранение общего дедуплицированного файла
            self.split_and_save_file('ТГ ', 'deduplicated', clean)
            
            # Сортировка и сохранение отдельно по каждому протоколу
            for proto in self.protocols:
                proto_lines = [l for l in clean if l.lower().startswith(f"{proto}://")]
                if proto_lines:
                    self.split_and_save_file('ТГ ', proto, proto_lines)

if __name__ == "__main__":
    TelegramRawCollector().collect()
