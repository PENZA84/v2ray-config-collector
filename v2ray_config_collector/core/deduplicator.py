import os
import hashlib
import sys
import re
import time
from collections import defaultdict

class ConfigDeduplicator:
    def __init__(self, input_file=None, output_dir=None):
        # --- ENGLISH PRODUCTION ENVIRONMENT NAVIGATION ---
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Берём сырьё, которое нагребли наши цеха в бункер
        self.input_file = input_file or os.path.join(package_dir, 'data', 'raw_incoming', 'deep_raw_collected.txt')
        self.output_dir = output_dir or os.path.join(package_dir, 'data', 'unique')
        
        # Твой оригинальный всеядный список из 23 протоколов! 👑
        self.protocols = [
            'socks5', 'socks4', 'socks', 'http', 'https', 'ss', 'trojan', 
            'vmess', 'vless', 'tuic', 'hysteria', 'hysteria2', 'hy2', 
            'anytls', 'naive', 'naive+https', 'juicity', 'trusttunnel', 
            'shadowtls', 'wireguard', 'wg', 'ssh'
        ]
        
        self.existing_hashes = set()
        self.incoming_lines = []
        
        # Статистика для нашего праздничного щита управления
        self.stats = {
            'total_incoming': 0,
            'duplicates_removed': 0,
            'new_unique_secured': 0
        }
        self.proto_stats = defaultdict(int)

    def generate_string_hash(self, line):
        """Создает уникальный хэш-слепок для очистки строки от дубликатов"""
        # Чистим от пробелов и приводим к нижнему регистру основную часть (до имени ноды #)
        clean_line = line.strip().split('#')[0].lower()
        return hashlib.md5(clean_line.encode('utf-8')).hexdigest()

    def load_existing_txt_database(self):
        """Загружает хэши из уже существующих TXT-файлов Трона, чтобы не собирать повторы"""
        os.makedirs(self.output_dir, exist_ok=True)
        
        for proto in self.protocols:
            safe_filename = proto.replace('+', '_')
            file_path = os.path.join(self.output_dir, f"{safe_filename}.txt")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line_str = line.strip()
                            if line_str and '://' in line_str:
                                h = self.generate_string_hash(line_str)
                                self.existing_hashes.add(h)
                except:
                    pass

        # Загружаем свежее сырьё из бункера сбора
        if os.path.exists(self.input_file):
            try:
                with open(self.input_file, 'r', encoding='utf-8') as f:
                    self.incoming_lines = [line.strip() for line in f if line.strip() and '://' in line.strip()]
                    self.stats['total_incoming'] = len(self.incoming_lines)
            except:
                pass
        return True

    def process_and_save_txt(self):
        """Чистит дубликаты на лету и раскладывает чистые TXT-строки по файлам протоколов"""
        proto_buckets = defaultdict(list)
        
        # Сортируем и дедуплицируем новые поступления
        for line in self.incoming_lines:
            h = self.generate_string_hash(line)
            
            if h not in self.existing_hashes:
                # Определяем протокол строки
                proto_found = 'unknown'
                for proto in self.protocols:
                    if line.lower().startswith(f"{proto}://"):
                        proto_found = proto
                        break
                
                if proto_found != 'unknown':
                    proto_buckets[proto_found].append(line)
                    self.existing_hashes.add(h) # Добавляем в базу знаний, чтоб не дублировать внутри цикла
                    self.stats['new_unique_secured'] += 1
                    self.proto_stats[proto_found] += 1
            else:
                self.stats['duplicates_removed'] += 1

        # Дописываем новые уникальные строки в соответствующие TXT файлы Трона
        for proto in self.protocols:
            new_lines = proto_buckets.get(proto, [])
            if not new_lines:
                continue
                
            safe_filename = proto.replace('+', '_')
            file_path = os.path.join(self.output_dir, f"{safe_filename}.txt")
            
            # Читаем старые строки, если они были, чтобы перезаписать объединенный отсортированный список
            existing_lines_in_file = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_lines_in_file = [l.strip() for l in f if l.strip()]
                except:
                    pass
            
            # Объединяем старое и новое в единый монолит
            combined_all = list(set(existing_lines_in_file + new_lines))
            
            # Атомарная безопасная запись ТХТ-контейнера на диск
            tmp_file = file_path + ".tmp"
            with open(tmp_file, 'w', encoding='utf-8') as out_f:
                out_f.write("\n".join(sorted(combined_all)) + "\n")
            os.replace(tmp_file, file_path)

        # Очищаем входной бункер сырья, так как смена отработана
        try:
            if os.path.exists(self.input_file):
                with open(self.input_file, 'w', encoding='utf-8') as f:
                    f.write("")
        except:
            pass

    def process(self):
        sys.stdout.reconfigure(line_buffering=True)
        print("🏭 [ЦЕХ ОГРАНКИ] Запуск ТХТ-Дедупликатора и Сортировщика Завода... 💎✨", flush=True)
        
        start_time = time.time()
        if self.load_existing_txt_database():
            self.process_and_save_txt()
            elapsed = time.time() - start_time
            
            # Наш потрясающий, красивейший приборный отчет! 📊🦖
            print("\n📊 " + "-"*20 + " ОТЧЁТ СОРТИРОВКИ СТРОК ДЛЯ Н И ТРОНА " + "-"*20, flush=True)
            print(f"📥 СВЕЖИХ СТРОК-КОНФИГОВ ИЗ БУНКЕРА: {self.stats['total_incoming']} шт.", flush=True)
            print(f"🧹 ПОВТОРЯЮЩИХСЯ ДУБЛИКАТОВ СТЕРТО: {self.stats['duplicates_removed']} шт.", flush=True)
            print(f"✨ ЧИСТЫХ НОВЫХ СТРОК НА КОНЦЕ ДОБАВЛЕНО: {self.stats['new_unique_secured']} шт. 💎", flush=True)
            print(f"⏱️ ВРЕМЯ СТРОКОВОЙ СОРТИРОВКИ: Цех отработал за {elapsed:.2f} сек.", flush=True)
            print("-" * 77, flush=True)
            
            # Выводим распределение по полочкам
            print("🗂️ ПОПОЛНЕНИЕ ТЕКСТОВЫХ ТХТ-КОНТЕЙНЕРОВ ДЛЯ Н:", flush=True)
            active_protos = {k: v for k, v in self.proto_stats.items() if v > 0}
            if active_protos:
                for p in sorted(active_protos.keys()):
                    print(f"   ↳ 📄 {p.upper()}.txt : +{active_protos[p]} новых чистых строк secured! 🤍", flush=True)
            else:
                print("   ℹ️ На этой смене все пришедшие строки уже были в нашей ТХТ-базе.", flush=True)
            print("====================================================================\n", flush=True)
            return True
        return False

if __name__ == "__main__":
    ConfigDeduplicator().process()
