import os
import re
import socket
import sys
import time
import requests
from urllib.parse import urlparse

# Интегрируем tqdm для красивого прогресс-бара, если он доступен в системе
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

class ConnectivityValidator:
    def __init__(self):
        # Строгая привязка к нашей единой структуре папок Завода
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.input_dir = os.path.join(self.base_dir, 'data', 'unique')
        self.output_dir = os.path.join(self.base_dir, 'data', 'validated')
        self.timeout = 8  # секунд на проверку соединения
        self.test_url = "https://www.gstatic.com/generate_204"  # надёжный адрес для проверки доступа
        self.max_ping = 300  # максимальное время ответа, чтобы считать рабочим
        os.makedirs(self.output_dir, exist_ok=True)

    def parse_proxy(self, link):
        """
        Разбирает ссылку прокси на составляющие: протокол, сервер, порт, данные для авторизации
        Поддерживает все форматы, которые мы собираем: vless, vmess, trojan, ss, hysteria2 и другие
        """
        try:
            if '://' not in link:
                return None, None, None, None
            
            # Отделяем протокол и всё остальное
            proto_part, rest = link.split('://', 1)
            proto = proto_part.lower().strip()

            # Убираем комментарий в конце ссылки
            if '#' in rest:
                rest, _ = rest.split('#', 1)

            # Отделяем данные для входа от хоста (если есть логин/пароль/uuid)
            auth = None
            if '@' in rest:
                auth, host_port = rest.rsplit('@', 1)
            else:
                host_port = rest

            # Получаем хост и порт, убираем параметры после знака ?
            if ':' in host_port:
                host, port_part = host_port.split(':', 1)
                port = port_part.split('?')[0].strip()
                return proto, host.strip(), int(port), auth
            
        except Exception:
            pass
        return None, None, None, None

    def test_tcp_connection(self, host, port):
        """
        Базовая проверка: открыт ли порт, доступен ли сервер по TCP
        Возвращает: статус (True/False), время ответа в мс
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            start_time = time.perf_counter()
            s.connect((host, port))
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            ping_ms = round((time.perf_counter() - start_time) * 1000)
            return True, ping_ms
        except socket.timeout:
            return False, 0
        except ConnectionRefusedError:
            return False, 0
        except Exception:
            return False, 0

    def test_proxy_functional(self, proto, host, port, auth=None):
        """
        Расширенная проверка: не только порт открыт, но и прокси реально работает, пропускает трафик
        Работает для http, https, socks4, socks5 — для остальных только TCP проверка
        Возвращает: статус, описание результата
        """
        if proto not in ['http', 'https', 'socks4', 'socks5']:
            return None, "ℹ️ Только TCP проверка (для этого протокола нет функциональной проверки)"

        try:
            # Формируем адрес прокси для библиотеки requests
            proxy_url = f"{proto}://"
            if auth:
                proxy_url += f"{auth}@"
            proxy_url += f"{host}:{port}"

            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

            start = time.perf_counter()
            r = requests.get(
                self.test_url,
                proxies=proxies,
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=False
            )
            resp_time = round((time.perf_counter() - start) * 1000)

            if r.status_code in (200, 204):
                return True, f"✅ Работает | Ответ: {resp_time}мс"
            else:
                return False, f"⚠️ Порт открыт, но прокси не отвечает правильно ({r.status_code})"

        except requests.exceptions.ProxyError:
            return False, "❌ Ошибка подключения к прокси"
        except requests.exceptions.Timeout:
            return False, "❌ Превышено время ожидания"
        except Exception as e:
            return False, f"❌ Ошибка: {str(e)[:30]}"

    def test_all_configs(self):
        """
        Основная функция валидации с гвардейской защитой от файлов-сборников
        """
        title4 = "Tests TCP connectivity of proxy configurations"
        print("\n" + "=" * len(title4))
        print(title4)
        print("=" * len(title4) + "\n")

        # Собираем все ссылки из всех файлов, которые мы насобирали
        all_links = []
        if not os.path.exists(self.input_dir):
            print("❌ Папка с конфигами не найдена")
            return

        for fname in os.listdir(self.input_dir):
            # ГВАРДЕЙСКИЙ ЩИТ: Полностью игнорируем файлы-сборники сырья!
            # Валидатор больше никогда не тронет deduplicated.txt и ТГ deduplicated.txt
            if 'deduplicated' in fname.lower():
                continue

            if fname.endswith('.txt'):
                fpath = os.path.join(self.input_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = [l.strip() for l in f if l.strip() and '://' in l]
                        all_links.extend(lines)
                except Exception:
                    continue

        if not all_links:
            print("❌ Нет конфигураций для проверки (сборники deduplicated под защитой)")
            return

        # Убираем дубликаты
        all_links = list(set(all_links))
        print(f"🔍 Найдено уникальных конфигураций для проверки: {len(all_links)}\n")

        # Разделяем на группы
        working_list = []       # Всё работает
        tcp_ok_not_func = []    # Порт открыт, но не работает
        dead_list = []          # Вообще недоступно
        fast_list = []          # Быстрые (меньше лимита)

        # Обертка в прогресс-бар tqdm для красивого отображения в GitHub Actions
        iterable = enumerate(all_links, 1)
        if tqdm:
            # Настраиваем бар: вывод в stdout, чтобы логи не ломались в облаке
            progress_bar = tqdm(iterable, total=len(all_links), desc="⚡ Валидация прокси", file=sys.stdout, leave=True)
        else:
            progress_bar = iterable

        # Проверяем каждую ссылку по очереди
        for idx, link in progress_bar:
            proto, host, port, auth = self.parse_proxy(link)
            if not proto or not host or not port:
                dead_list.append(link)
                if not tqdm:
                    print(f"[{idx}/{len(all_links)}] ❌ Неверный формат | {link[:70]}...")
                continue

            # Шаг 1: Проверяем TCP соединение
            tcp_status, ping = self.test_tcp_connection(host, port)

            if not tcp_status:
                dead_list.append(link)
                if not tqdm:
                    print(f"[{idx}/{len(all_links)}] ❌ TCP недоступен | {proto} | {host}:{port}")
                continue

            # Шаг 2: Если TCP открыт — проверяем работает ли как прокси
            func_status, note = self.test_proxy_functional(proto, host, port, auth)

            if func_status is True:
                working_list.append(link)
                if ping < self.max_ping:
                    fast_list.append(link)
                if not tqdm:
                    print(f"[{idx}/{len(all_links)}] ✅ РАБОТАЕТ | {proto:<10} | {host}:{port:<20} | пинг: {ping:>3}мс | {note}")
            elif func_status is False:
                tcp_ok_not_func.append(link)
                if not tqdm:
                    print(f"[{idx}/{len(all_links)}] ⚠️ ЧАСТИЧНО | {proto:<10} | {host}:{port:<20} | пинг: {ping:>3}мс | {note}")
            else:
                # Для протоколов без функциональной проверки — просто записываем как рабочие по TCP
                working_list.append(link)
                if not tqdm:
                    print(f"[{idx}/{len(all_links)}] ✅ TCP OK    | {proto:<10} | {host}:{port:<20} | пинг: {ping:>3}мс | {note}")

        # === СОХРАНЯЕМ РЕЗУЛЬТАТЫ ===
        def save_file(name, items):
            if items:
                with open(os.path.join(self.output_dir, name), 'w', encoding='utf-8') as f:
                    f.write("\n".join(items))

        # Общие списки
        save_file("✅ Все рабочие.txt", working_list)
        save_file("⚡ Быстрые (менее {}мс).txt".format(self.max_ping), fast_list)
        save_file("⚠️ Порт открыт но не работает.txt", tcp_ok_not_func)
        save_file("❌ Нерабочие.txt", dead_list)

        # Рабочие по протоколам
        protocols = ['vless', 'vmess', 'trojan', 'ss', 'hysteria2', 'tuic', 'naive+https', 'http', 'https', 'socks5']
        for p in protocols:
            plist = [l for l in working_list if l.lower().startswith(f"{p}://")]
            save_file(f"✅ {p.upper()} рабочие.txt", plist)

        # === ИТОГОВАЯ СТАТИСТИКА ===
        print("\n📊 === ИТОГ ПРОВЕРКИ ЦЕХА ===")
        print(f"🔎 Всего проверено:      {len(all_links)}")
        print(f"✅ Полностью рабочих:    {len(working_list)} 🤍")
        print(f"⚡ Из них быстрых:       {len(fast_list)} 🔥")
        print(f"⚠️ Частично рабочих:     {len(tcp_ok_not_func)} ✨")
        print(f"❌ Нерабочих:            {len(dead_list)} 💤")
        print(f"💾 Результаты бережно сохранены в: data/validated/")
        print("=" * 30 + "\n")

if __name__ == "__main__":
    validator = ConnectivityValidator()
    validator.test_all_configs()
