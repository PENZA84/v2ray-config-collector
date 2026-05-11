# ... твои импорты и вспомогательные функции parse_server_port остаются прежними ...

class FormatConverter:
    def __init__(self, input_files=None, output_file=None):
        # ... начало твоего __init__ ...
        self.stats = {
            'total_configs': 0, 'successful_conversions': 0, 'failed_conversions': 0,
            'filtered_configs': 0, 'vmess_count': 0, 'vless_count': 0,
            'trojan_count': 0, 'ss_count': 0, 'ssr_count': 0,
            'tuic_count': 0, 'hysteria_count': 0,
            # ДОБАВЛЯЕМ НОВЫЕ ГРУППЫ СЧЕТЧИКОВ
            'proxy_count': 0, # SOCKS, HTTP
            'advanced_count': 0, # Juicity, Naive, Wireguard и др.
            'other_count': 0
        }
        # ...

    def detect_protocol(self, config_line):
        line = config_line.lower()
        # Стандартные V2Ray/Xray
        if line.startswith('vmess://'): return 'vmess'
        if line.startswith('vless://'): return 'vless'
        if line.startswith('trojan://'): return 'trojan'
        if line.startswith('ss://'): return 'shadowsocks'
        if line.startswith('ssr://'): return 'ssr'
        if line.startswith('tuic://'): return 'tuic'
        if line.startswith(('hysteria2://', 'hy2://')): return 'hysteria2'
        if line.startswith('hysteria://'): return 'hysteria'
        
        # ТВОЙ РАСШИРЕННЫЙ СПИСОК:
        if line.startswith(('socks5://', 'socks4://')): return 'socks'
        if line.startswith(('http://', 'https://')):
            if not any(line.endswith(ext) for ext in ['.txt', '.sub', '.php', '.yaml']):
                return 'http'
        
        # Продвинутые и новые протоколы
        advanced_protocols = [
            'wireguard://', 'ssh://', 'juicity://', 'naive://', 
            'trusttunnel://', 'shadowtls://', 'anytls://'
        ]
        for proto in advanced_protocols:
            if line.startswith(proto):
                return proto.replace('://', '')
                
        return 'unknown'

    def parse_universal_proxy(self, config_url, protocol_type):
        """Универсальный метод для всех новых протоколов из твоего списка"""
        try:
            # Отсекаем всё лишнее для получения адреса и параметров
            clean_part = config_url.split('://')[-1]
            remarks = ""
            if '#' in clean_part:
                clean_part, remarks = clean_part.split('#', 1)
                remarks = urllib.parse.unquote(remarks)

            # Выделяем авторизацию и хост:порт
            auth = ""
            address_part = clean_part
            if '@' in clean_part:
                auth, address_part = clean_part.split('@', 1)

            server, port = parse_server_port(address_part)

            # Статистика
            if protocol_type in ['socks', 'http']:
                self.stats['proxy_count'] += 1
            else:
                self.stats['advanced_count'] += 1

            return {
                'type': protocol_type,
                'server': server,
                'port': port,
                'auth': auth,
                'remarks': remarks or f"{protocol_type}_{server}",
                'raw_config': config_url
            }
        except:
            return None

    def parse_config_with_reason(self, config_line):
        config_line = config_line.strip()
        if not config_line or config_line.startswith('#'):
            return None, 'empty_or_comment'
        
        protocol = self.detect_protocol(config_line)
        
        # Если протокол из нашего нового расширенного списка — работаем!
        extended_list = [
            'socks', 'http', 'hysteria', 'wireguard', 'ssh', 
            'juicity', 'naive', 'trusttunnel', 'shadowtls', 'anytls'
        ]
        
        if protocol in extended_list:
            result = self.parse_universal_proxy(config_line, protocol)
            return result, None if result else f'{protocol}_parse_failed'

        # Твоя оригинальная логика для старых протоколов
        if protocol == 'vmess':
            result = self.parse_vmess(config_line)
            return result, None if result else 'vmess_parse_failed'
        # ... (vless, trojan, ss, ssr, tuic, hysteria2 — оставляешь как было) ...
        
        self.stats['other_count'] += 1
        self.failure_reasons['unknown_protocol'] += 1
        return None, 'unknown_protocol'

    # Не забудь обновить вывод в print_summary, чтобы видеть результат по всем!
