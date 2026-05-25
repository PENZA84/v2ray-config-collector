import os
import re
import base64

try:
    import yaml
    YAML_READY = True
except ImportError:
    YAML_READY = False

class FormatParser:
    def __init__(self):
        # Строгая привязка к нашей идеальной структуре
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.max_file_size_mb = 40
        
        # Полный список протоколов для Throne и v2rayN
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2', 
            'anytls', 'naive', 'naive+https', 'juicity', 'trusttunnel', 
            'shadowtls', 'wireguard', 'wg', 'ssh'
        ]
        
        proto_pattern = '|'.join([re.escape(p) for p in self.protocols])
        self.regex_pattern = re.compile(r'(?:' + proto_pattern + r')://[^\s<"\']+')

    def extract_from_yaml(self, content):
        """Глубокий парсинг Clash YAML конфигураций"""
        if not YAML_READY:
            return []
        extracted = []
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict) and 'proxies' in data:
                for p in data['proxies']:
                    t = p.get('type', '').lower()
                    # Приведение типов к стандартам Throne/v2rayN
                    if t == 'shadowsocks': t = 'ss'
                    
                    server = p.get('server')
                    port = p.get('port')
                    uuid = p.get('uuid') or p.get('password')
                    name = p.get('name', 'clash').replace(' ', '_')
                    
                    if all([t, server, port, uuid]) and t in self.protocols:
                        link = f"{t}://{uuid}@{server}:{port}#{name}"
                        extracted.append(link)
        except:
            pass 
        return extracted

    def decode_base64_content(self, content):
        """Декодирование подписок, если они зашифрованы в Base64"""
        try:
            # Очистка от пробелов и возможных артефактов
            clean_content = content.strip().replace("\n", "").replace("\r", "")
            decoded = base64.b64decode(clean_content).decode('utf-8', errors='ignore')
            if any(proto in decoded for proto in ['vless://', 'vmess://', 'ss://', 'trojan://']):
                return decoded
        except:
            pass
        return content

    def split_and_save_file(self, base_name, lines):
        """Сохранение раздельных файлов по 40 МБ без создания общего мусора"""
        if not lines: 
            return
        
        # Проверяем, существует ли папка, перед очисткой старых файлов этого протокола
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f == f"{base_name}.txt" or re.match(r'^' + re.escape(base_name) + r'\s+\d+\.txt$', f):
                    try: os.remove(os.path.join(self.output_dir, f))
                    except: pass

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

        for idx, chunk_lines in enumerate(parts):
            if idx == 0:
                part_file = os.path.join(self.output_dir, f"{base_name}.txt")
            else:
                part_file = os.path.join(self.output_dir, f"{base_name} {idx}.txt")
            
            with open(part_file, 'w', encoding='utf-8') as pf:
                pf.write("\n".join(chunk_lines))

    def parse_and_distribute(self, raw_text, file_prefix=''):
        """Парсинг сырого текста, извлечение ссылок и раскладка по полкам unique"""
        if not raw_text:
            return
        
        # Попытка расшифровать Base64, если прилетел закодированный пул
        decoded_text = self.decode_base64_content(raw_text)
        
        configs = []
        # 1. Извлекаем стандартные ссылки
        configs.extend(self.regex_pattern.findall(decoded_text))
        
        # 2. Если внутри YAML (Clash), вытаскиваем прокси оттуда
        if 'proxies:' in decoded_text:
            configs.extend(self.extract_from_yaml(decoded_text))
            
        if not configs:
            return

        # Чистим дубликаты
        clean_configs = list(set([c.strip() for c in configs if c.strip()]))
        os.makedirs(self.output_dir, exist_ok=True)

        # Раскладываем строго по отдельным файлам-протоколам
        for proto in self.protocols:
            proto_lines = [l for l in clean_configs if l.lower().startswith(f"{proto}://")]
            if proto_lines:
                # Если передан префикс (например 'ТГ '), файлы назовутся 'ТГ vless.txt'
                self.split_and_save_file(f"{file_prefix}{proto}", proto_lines)

        print(f"[INFO] [PARSER] Глубокий разбор завершен. Конфиги распределены по полкам /unique/.")

if __name__ == "__main__":
    # Тестовый холостой запуск модуля
    FormatParser().parse_and_distribute("")
