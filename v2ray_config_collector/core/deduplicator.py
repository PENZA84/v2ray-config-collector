import json
import os
import hashlib
import sys
from datetime import datetime
from collections import defaultdict
from tqdm import tqdm
import time

class ConfigDeduplicator:
    def __init__(self, input_file=None, output_dir=None):
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if input_file is None:
            input_file = os.path.join(package_dir, 'data', 'processed', 'normalized_configs.json')
        if output_dir is None:
            output_dir = os.path.join(package_dir, 'data', 'unique')
        self.input_file = input_file
        self.output_dir = output_dir
        self.stats = {
            'total_configs': 0,
            'unique_configs': 0,
            'duplicates_removed': 0,
            'protocols': defaultdict(int),
            'duplicate_groups': 0,
            'existing_loaded': 0
        }
        self.configs = []
        self.unique_configs = []
        self.duplicate_groups = []
        self.existing_hashes = set()

    def load_configs(self):
        """ Загружает базу и входящие конфиги, предотвращая затирание ручной нарезки """
        try:
            # Шаг 1: Поднимаем уже существующую базу уникальных конфигов
            existing_json_path = os.path.join(self.output_dir, 'deduplicated.json')
            if os.path.exists(existing_json_path):
                print(f"📦 Обнаружена существующая база. Загружаем сохраненные конфиги...")
                try:
                    with open(existing_json_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    
                    existing_list = existing_data.get('configs', []) if isinstance(existing_data, dict) else []
                    
                    # Старые уникальные конфиги добавляем СРАЗУ как уникальные, без фильтрации
                    for ext_conf in existing_list:
                        ex_hash = self.generate_config_hash(ext_conf)
                        self.unique_configs.append(ext_conf)
                        self.existing_hashes.add(ex_hash)
                            
                    self.stats['existing_loaded'] = len(existing_list)
                    print(f"✅ Успешно сохранено из базы: {self.stats['existing_loaded']:,} уникальных элементов (включая ручную нарезку).")
                except Exception as ex_load:
                    print(f"⚠️ Ошибка при чтении существующей базы: {ex_load}")

            # Шаг 2: Загружаем порцию новых нормализованных конфигов из текущего конвейера
            if not os.path.exists(self.input_file):
                print(f"❌ Файл свежей порции {self.input_file} не найден!")
                return len(self.unique_configs) > 0
                
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if 'configs' in data:
                self.configs = data['configs']
            else:
                self.configs = data if isinstance(data, list) else []
                
            self.stats['total_configs'] = len(self.configs)
            for config in self.configs:
                protocol = config.get('type', 'unknown')
                self.stats['protocols'][protocol] += 1
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки файлов конвейера: {e}")
            return False

    def generate_config_hash(self, config):
        """ Строгий хэш: учитывает имя (remarks) и пароли/uuid, чтобы не сливать ручную нарезку """
        protocol = config.get('type', 'unknown')
        key_parts = [f"type:{protocol}"]
        
        # Основные сетевые параметры
        for field in ['server', 'port', 'uuid', 'password', 'remarks', 'path', 'host', 'sni', 'tls']:
            val = config.get(field, '')
            if val:
                key_parts.append(f"{field}:{str(val).strip()}")
                
        # Если есть сырой конфиг, подмешиваем ключевые параметры оттуда для точности
        if 'raw_config' in config and isinstance(config['raw_config'], dict):
            raw = config['raw_config']
            for raw_field in ['ps', 'add', 'id', 'host', 'path']:
                if raw.get(raw_field):
                    key_parts.append(f"raw_{raw_field}:{str(raw[raw_field]).strip()}")

        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def find_duplicates(self):
        if not self.configs:
            print("ℹ️ Нет новых конфигураций для анализа.")
            self.stats['unique_configs'] = len(self.unique_configs)
            return

        print("🪐 Начинаем дедупликацию нового прихода...")
        start_time = time.time()
        hash_to_configs = defaultdict(list)
        
        print("Phase 1: Генерируем цифровые слепки...")
        for i, config in enumerate(tqdm(self.configs, desc="🧬 Индексация прихода", unit="config", file=sys.stdout)):
            config_hash = self.generate_config_hash(config)
            config['_hash'] = config_hash
            config['_original_index'] = i
            
            # Если такой СТРОГИЙ хэш уже есть в базе, это полный дубликат
            if config_hash in self.existing_hashes:
                self.stats['duplicates_removed'] += 1
                continue
                
            hash_to_configs[config_hash].append(config)
            
        if not hash_to_configs:
            print("✨ Новые файлы не принесли уникальных хэшей (все элементы уже известны базе).")
            self.stats['unique_configs'] = len(self.unique_configs)
            return

        print("\nPhase 2: Очистка внутренних дубликатов нового прихода...")
        sys.stdout.flush()
        time.sleep(0.1)
        
        for config_hash, configs_group in tqdm(hash_to_configs.items(), desc="🧹 Фильтрация", unit="group", file=sys.stdout):
            if len(configs_group) > 1:
                self.duplicate_groups.append(configs_group)
                self.stats['duplicate_groups'] += 1
                
                best_config = self.select_best_config(configs_group)
                self.unique_configs.append(best_config)
                self.existing_hashes.add(config_hash)
                
                removed_count = len(configs_group) - 1
                self.stats['duplicates_removed'] += removed_count
            else:
                self.unique_configs.append(configs_group[0])
                self.existing_hashes.add(config_hash)
                
        self.stats['unique_configs'] = len(self.unique_configs)
        total_time = time.time() - start_time
        print(f"\n📊 Итоги обработки: Из новых {self.stats['total_configs']:,} сохранено уникальных: {len(hash_to_configs):,}")
        print(f"   Общий размер объединенной базы теперь: {self.stats['unique_configs']:,} конфигов.")

    def select_best_config(self, configs_group):
        def config_score(config):
            score = 0
            if config.get('remarks') and config.get('remarks').strip():
                score += 10
            filled_fields = sum(1 for v in config.values() if v and str(v).strip() and not str(v).startswith('_'))
            score += filled_fields
            score += config.get('_original_index', 0) * 0.01
            return score
        return max(configs_group, key=config_score)

    def save_all_configs(self):
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            output_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'source_file': self.input_file,
                    'total_base_configs': self.stats['unique_configs'],
                    'duplicates_removed_this_run': self.stats['duplicates_removed']
                },
                'configs': [self.clean_config(config) for config in self.unique_configs]
            }
            
            all_configs_file = os.path.join(self.output_dir, 'deduplicated.json')
            with open(all_configs_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            sys.stdout.flush()
            time.sleep(0.1)
            
            all_configs_txt = os.path.join(self.output_dir, 'deduplicated.txt')
            with open(all_configs_txt, 'w', encoding='utf-8') as f:
                f.write(f"Unique V2Ray Configs - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total unique configs: {self.stats['unique_configs']}\n\n")
                for config in tqdm(self.unique_configs, desc="📝 Сборка общего TXT файла", unit="config", file=sys.stdout, leave=False):
                    url = self.reconstruct_config_url(config)
                    if url:
                        f.write(f"{url}\n")
            print(f"💾 Файлы базы успешно обновлены. Нарезка защищена!")
        except Exception as e:
            print(f"❌ Ошибка при записи общих файлов базы: {e}")

    def save_by_protocol(self):
        try:
            protocols_dir = os.path.join(self.output_dir, 'protocols')
            os.makedirs(protocols_dir, exist_ok=True)
            
            protocol_groups = defaultdict(list)
            for config in self.unique_configs:
                protocol = config.get('type', 'unknown')
                protocol_groups[protocol].append(config)
                
            for protocol, configs in protocol_groups.items():
                protocol_file = os.path.join(protocols_dir, f'{protocol}_configs.json')
                protocol_data = {
                    'metadata': {'protocol': protocol, 'generated_at': datetime.now().isoformat(), 'total_configs': len(configs)},
                    'configs': [self.clean_config(config) for config in configs]
                }
                with open(protocol_file, 'w', encoding='utf-8') as f:
                    json.dump(protocol_data, f, ensure_ascii=False, indent=2)
                    
                protocol_txt = os.path.join(protocols_dir, f'{protocol}_configs.txt')
                with open(protocol_txt, 'w', encoding='utf-8') as f:
                    f.write(f"{protocol.upper()} Configs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    for config in configs:
                        url = self.reconstruct_config_url(config)
                        if url:
                            f.write(f"{url}\n")
        except Exception as e:
            print(f"❌ Ошибка распределения по папкам протоколов: {e}")

    def clean_config(self, config):
        cleaned = config.copy()
        for key in list(cleaned.keys()):
            if key.startswith('_'):
                del cleaned[key]
        return cleaned

    def reconstruct_config_url(self, config):
        try:
            protocol = config.get('type', '')
            if protocol == 'vmess': return self.reconstruct_vmess_url(config)
            elif protocol == 'vless': return self.reconstruct_vless_url(config)
            elif protocol == 'trojan': return self.reconstruct_trojan_url(config)
            elif protocol == 'shadowsocks': return self.reconstruct_shadowsocks_url(config)
            elif protocol == 'ssr': return self.reconstruct_ssr_url(config)
            elif protocol == 'tuic': return self.reconstruct_tuic_url(config)
            elif protocol == 'hysteria2': return self.reconstruct_hysteria2_url(config)
            return None
        except Exception:
            return None

    def reconstruct_vmess_url(self, config):
        try:
            import base64
            if 'raw_config' in config and isinstance(config['raw_config'], dict):
                raw_config_copy = config['raw_config'].copy()
                if config.get('remarks'): raw_config_copy['ps'] = config['remarks']
                raw_json = json.dumps(raw_config_copy, separators=(',', ':'))
                return f"vmess://{base64.b64encode(raw_json.encode('utf-8')).decode('utf-8')}"
            vmess_data = {
                'v': '2', 'ps': config.get('remarks', ''), 'add': config.get('server', ''),
                'port': str(config.get('port', 443)), 'id': config.get('uuid', ''),
                'aid': str(config.get('alterId', 0)), 'scy': config.get('cipher', 'auto'),
                'net': config.get('network', 'tcp'), 'type': config.get('type_network', ''),
                'host': config.get('host', ''), 'path': config.get('path', ''),
                'tls': config.get('tls', ''), 'sni': config.get('sni', ''),
                'alpn': config.get('alpn', ''), 'fp': config.get('fingerprint', '')
            }
            raw_json = json.dumps(vmess_data, separators=(',', ':'))
            return f"vmess://{base64.b64encode(raw_json.encode('utf-8')).decode('utf-8')}"
        except Exception: return None

    def reconstruct_vless_url(self, config):
        try:
            import urllib.parse
            params = {}
            for f, p in [('flow','flow'), ('encryption','encryption'), ('network','type'), ('tls','security'), ('sni','sni'), ('path','path'), ('host','host'), ('alpn','alpn'), ('fingerprint','fp')]:
                if config.get(f): params[p] = config[f]
            query = f"?{urllib.parse.urlencode(params)}" if params else ''
            frag = f"#{urllib.parse.quote(config['remarks'])}" if config.get('remarks') else ''
            return f"vless://{config.get('uuid', '')}@{config.get('server', '')}:{config.get('port', 443)}{query}{frag}"
        except Exception: return None

    def reconstruct_trojan_url(self, config):
        try:
            import urllib.parse
            params = {}
            for f, p in [('sni','sni'), ('alpn','alpn'), ('fingerprint','fp'), ('network','type'), ('path','path'), ('host','host')]:
                if config.get(f): params[p] = config[f]
            if config.get('allowInsecure'): params['allowInsecure'] = '1'
            query = f"?{urllib.parse.urlencode(params)}" if params else ''
            frag = f"#{urllib.parse.quote(config['remarks'])}" if config.get('remarks') else ''
            return f"trojan://{config.get('password', '')}@{config.get('server', '')}:{config.get('port', 443)}{query}{frag}"
        except Exception: return None

    def reconstruct_shadowsocks_url(self, config):
        try:
            import base64, urllib.parse
            auth = base64.b64encode(f"{config.get('method', 'aes-256-gcm')}:{config.get('password', '')}".encode('utf-8')).decode('utf-8')
            frag = f"#{urllib.parse.quote(config['remarks'])}" if config.get('remarks') else ''
            return f"ss://{auth}@{config.get('server', '')}:{config.get('port', 8080)}{frag}"
        except Exception: return None

    def reconstruct_ssr_url(self, config):
        try:
            import base64
            p_b64 = base64.b64encode(config.get('password', '').encode('utf-8')).decode('utf-8')
            main = f"{config.get('server', '')}:{config.get('port', 8080)}:{config.get('protocol', 'origin')}:{config.get('method', 'aes-256-cfb')}:{config.get('obfs', 'plain')}:{p_b64}"
            params = []
            for f, k in [('obfs_param', 'obfsparam'), ('protocol_param', 'protoparam'), ('remarks', 'remarks'), ('group', 'group')]:
                if config.get(f): params.append(f"{k}={base64.b64encode(config[f].encode('utf-8')).decode('utf-8')}")
            full = f"{main}/?{'&'.join(params)}" if params else main
            return f"ssr://{base64.b64encode(full.encode('utf-8')).decode('utf-8')}"
        except Exception: return None

    def reconstruct_tuic_url(self, config):
        try:
            import urllib.parse
            params = {}
            for f in ['version', 'alpn', 'sni', 'congestion_control', 'udp_relay_mode']:
                if config.get(f): params[f] = config[f]
            if config.get('allowInsecure'): params['allowInsecure'] = '1'
            query = f"?{urllib.parse.urlencode(params)}" if params else ''
            frag = f"#{urllib.parse.quote(config['remarks'])}" if config.get('remarks') else ''
            auth = f"{config.get('uuid', '')}:{config.get('password', '')}" if config.get('password') else config.get('uuid', '')
            return f"tuic://{auth}@{config.get('server', '')}:{config.get('port', 443)}{query}{frag}"
        except Exception: return None

    def reconstruct_hysteria2_url(self, config):
        try:
            import urllib.parse
            params = {}
            for f, p in [('sni','sni'), ('pinSHA256','pinSHA256'), ('obfs','obfs'), ('obfs_password','obfs-password'), ('up','up'), ('down','down'), ('alpn','alpn')]:
                if config.get(f): params[p] = config[f]
            if config.get('insecure'): params['insecure'] = '1'
            query = f"?{urllib.parse.urlencode(params)}" if params else ''
            frag = f"#{urllib.parse.quote(config['remarks'])}" if config.get('remarks') else ''
            return f"hysteria2://{config.get('auth', '')}@{config.get('server', '')}:{config.get('port', 443)}{query}{frag}"
        except Exception: return None

    def process(self):
        try:
            if not self.load_configs(): return False
            self.find_duplicates()
            self.save_all_configs()
            self.save_by_protocol()
            return True
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            return False

def main():
    deduplicator = ConfigDeduplicator()
    deduplicator.process()

if __name__ == "__main__":
    main()
