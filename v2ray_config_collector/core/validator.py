import os
import socket
import sys
import re
import base64
import json
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

class ConnectivityValidator:
    def __init__(self):
        # 📂 КОРЕНЬ ЗАВОДА: выходим из папки 'core' на один уровень вверх в корень репозитория
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Входной файл из папки unique в корне репозитория (тот самый тяжелый гигант)
        self.input_file = os.path.join(self.base_dir, 'data', 'unique', 'deduplicated.txt')
        
        # 📂 ПАПКА ДЛЯ ПОЛНОГО РАЗДЕЛЬНОГО СКЛАДА ВСЕХ ПРОТОКОЛОВ
        self.output_dir = os.path.join(self.base_dir, 'data', 'validated')
        
        self.timeout = 4  
        self.max_workers = 100 
        
        # ✂️ ЛИМИТ СТРОК ДЛЯ НАРЕЗКИ: файлы больше 40 000 строк будут пилиться на части,
        # чтобы весить не больше 20-30 МБ и не блокировать пуш на Гитхаб!
        self.max_lines_per_file = 40000
        
        # 🛡️ БАЗА ДЛЯ ДЕДУПЛИКАЦИИ ЯДРА (Сюда сохраняем уникальные UUID / ключи / логины)
        self.seen_cores = set()

    def extract_sing_box_core_id(self, config_text):
        """
        🤖 ДВИЖОК ЯДРА: Универсальный выковыриватель уникальных ключей и UUID.
        Намертво отсекает одинаковые сервера, какой бы протокол из 16 ни попался в Телеграме!
        """
        config_text = config_text.strip().replace('"', '').replace(',', '')
        try:
            # 1. Разбор NaïveProxy, TUIC, Juicity, Hysteria/Hysteria2
            if any(config_text.startswith(p) for p in ["naive", "tuic", "juicity", "hysteria", "hy2"]):
                match = re.search(r'(?:naive(?:\+https)?|tuic|juicity|hysteria2|hysteria|hy2)://([a-zA-Z0-9_\-\=\+:]+)@', config_text)
                if match:
                    return match.group(1)

            # 2. Разбор VMESS (Декодируем Base64 и вытаскиваем уникальный "id")
            elif config_text.startswith("vmess://"):
                raw_b64 = config_text.replace("vmess://", "")
                raw_b64 += "=" * ((4 - len(raw_b64) % 4) % 4)  # Фикс паддинга Base64
                decoded_bytes = base64.b64decode(raw_b64)
                data_json = json.loads(decoded_bytes.decode('utf-8', errors='ignore'))
                return str(data_json.get("id", config_text))
                
            # 3. Разбор VLESS / TROJAN / SSH
            elif any(config_text.startswith(p) for p in ["vless", "trojan", "ssh"]):
                match = re.search(r'(?:vless|trojan|ssh)://([a-zA-Z0-9_\-\=]+)@', config_text)
                if match:
                    return match.group(1)
                    
            # 4. Разбор SHADOWSOCKS / ShadowTLS / TrustTunnel / AnyTLS
            elif any(config_text.startswith(p) for p in ["ss", "shadowsocks", "shadowtls", "trusttunnel", "anytls"]):
                match = re.search(r'(?:ss|shadowsocks|shadowtls|trusttunnel|anytls)://([a-zA-Z0-9_\-\=\+]+)@', config_text)
                if match:
                    return match.group(1)
                    
            # 5. Разбор SOCKS / HTTP / HTTPS / WIREGUARD
            elif any(config_text.startswith(p) for p in ["socks", "http", "https", "wireguard", "wg"]):
                clean_config = config_text.split('#')[0]
                parsed = urlparse(clean_config)
                return parsed.netloc if parsed.netloc else config_text
        except Exception:
            pass
        return config_text

    def get_protocol_filename_base(self, config_text):
        """
        🔍 РАСПРЕДЕЛИТЕЛЬНЫЙ ЦЕХ: Анализирует ссылку и выдает БАЗОВОЕ имя (без расширения)
        под каждый из 16 протоколов твоего царского списка!
        """
        cfg = config_text.lower().strip()
        
        if cfg.startswith("vless://"):
            return "vless"
        elif cfg.startswith("vmess://"):
            return "vmess"
        elif cfg.startswith("naive") or "naive" in cfg:
            return "naive"
        elif cfg.startswith("hysteria2://") or cfg.startswith("hy2://"):
            return "hysteria2"
        elif cfg.startswith("hysteria://"):
            return "hysteria"
        elif cfg.startswith("tuic://"):
            return "tuic"
        elif cfg.startswith("juicity://"):
            return "juicity"
        elif cfg.startswith("trojan://"):
            return "trojan"
        elif cfg.startswith("ss://") or cfg.startswith("shadowsocks://"):
            return "shadowsocks"
        elif cfg.startswith("shadowtls://"):
            return "shadowtls"
        elif cfg.startswith("trusttunnel://"):
            return "trusttunnel"
        elif cfg.startswith("anytls://"):
            return "anytls"
        elif cfg.startswith("wireguard://") or cfg.startswith("wg://"):
            return "wireguard"
        elif cfg.startswith("ssh://"):
            return "ssh"
        elif cfg.startswith("socks") or cfg.startswith("socks5://"):
            return "socks"
        elif cfg.startswith("http://") or cfg.startswith("https://"):
            return "http"
        else:
            return "other_protocols"

    def parse_address(self, config):
        """Парсер хоста и порта, справляющийся с любым хаосом из Телеграма"""
        try:
            config = config.strip()
            if "://" in config:
                clean_config = config.split('#')[0]
                parsed = urlparse(clean_config)
                netloc = parsed.netloc
            else:
                netloc = config

            if '@' in netloc:
                address = netloc.rsplit('@', 1)[1]
            else:
                address = netloc
            
            address = address.split('?')[0].split('/')[0]
            
            if ':' in address:
                host, port = address.rsplit(':', 1)
                host = host.strip('[]')
                return host, int(port)
        except Exception:
            pass
        return None, None

    def check_tcp(self, config):
        """Проверка доступности порта сервера через сокет"""
        host, port = self.parse_address(config)
        if not host or not port:
            return None
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                return config
        except Exception:
            return None

    def test_all_configs(self):
        print(f"\n👑 [VALIDATOR] Абсолютный распределитель 16 протоколов с автонарезкой баз запущен...")
        print("📡 Радары Телеграм-цеха сканируют входящие потоки.")
        
        if not os.path.exists(self.input_file):
            print(f"❌ ОШИБКА: Входной файл {self.input_file} не найден!")
            return

        with open(self.input_file, 'r', encoding='utf-8') as f:
            raw_configs = [line.strip() for line in f if line.strip()]

        if not raw_configs:
            print("📭 На входе пусто. Нечего сортировать.")
            return

        # 1. ПРИМЕНЕНИЕ АЛГОРИТМОВ ЯДРА: Полная зачистка от дубликатов
        unique_by_core = []
        duplicate_cores_count = 0
        
        for cfg in raw_configs:
            core_key = self.extract_sing_box_core_id(cfg)
            if core_key in self.seen_cores:
                duplicate_cores_count += 1
                continue
            self.seen_cores.add(core_key)
            unique_by_core.append(cfg)

        print(f"📥 Считано из кучи Телеграма: {len(raw_configs)} ссылок.")
        print(f"🛡️ Движок срезал повторяющихся серверов: {duplicate_cores_count} шт.")
        print(f"⚡ Отправлено на финальный тест портов: {len(unique_by_core)} серверов.")
        
        # 2. Быстрая многопоточная проверка портов
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(tqdm(executor.map(self.check_tcp, unique_by_core), 
                                total=len(unique_by_core), 
                                desc="Проверка портов",
                                leave=True))
            
        valid_configs = [r for r in results if r is not None]

        # 3. 📂 СОРТИРОВКА И УМНАЯ НАРЕЗКА НА ЧАСТИ ДЛЯ БЕЗОПАСНОСТИ ГИТА
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Группируем ссылки по базовому имени протокола
        protocols_vault = {}
        for config in valid_configs:
            base_name = self.get_protocol_filename_base(config)
            if base_name not in protocols_vault:
                protocols_vault[base_name] = []
            protocols_vault[base_name].append(config)
            
        print(f"\n📦 РЕЗУЛЬТАТЫ СОРТИРОВКИ И НАРЕЗКИ ПО СКЛАДАМ:")
        for base_name, configs_list in protocols_vault.items():
            total_configs = len(configs_list)
            
            # Сценарий А: Конфигов немного — сохраняем одним аккуратным цельным файлом
            if total_configs <= self.max_lines_per_file:
                file_path = os.path.join(self.output_dir, f"{base_name}.txt")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(configs_list))
                print(f" 📑 {base_name.upper()}.TXT -> {total_configs} шт. (Цельный файл)")
            
            # Сценарий Б: База гигантская — режем на безопасные куски part1, part2...
            else:
                part_num = 1
                for i in range(0, total_configs, self.max_lines_per_file):
                    chunk = configs_list[i:i + self.max_lines_per_file]
                    file_path = os.path.join(self.output_dir, f"{base_name}_part{part_num}.txt")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(chunk))
                    print(f" ✂️ {base_name.upper()}_PART{part_num}.TXT -> {len(chunk)} шт. (Нарезанный кусок)")
                    part_num += 1

        print(f"\n==========================================================================")
        print(f"🏁 СУПЕР-КОНВЕЙЕР УСПЕШНО НАКАЧАЛ, ОТФИЛЬТРОВАЛ И НАРЕЗАЛ БАЗУ!")
        print(f"🏆 Всего живых серверов разложено: {len(valid_configs)}")
        print(f"📂 Все файлы ждут тебя в корневой папке: data/validated/ 💋")
        print(f"==========================================================================")

if __name__ == "__main__":
    validator = ConnectivityValidator()
    validator.test_all_configs()
