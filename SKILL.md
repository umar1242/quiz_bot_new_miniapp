# SKILL: Запуск Python Telegram-бота на Android через Termux

Пошаговая, повторно используемая инструкция: как развернуть и держать запущенным
Python Telegram-бота (aiogram) на Android-телефоне через Termux + proot-distro Ubuntu,
с автозапуском и Claude Code внутри.

Проверено на: Android (aarch64), Termux + proot-distro Ubuntu, Python 3.14 (glibc),
бот в `/root/quiz_bot_patched`.

---

## 0. Обзор архитектуры

```
Android (телефон)
└── Termux (Android-приложение, окружение musl)
    ├── sshd на порту 8022        ← заходим с компа по SSH
    ├── Termux:Boot               ← автозапуск при включении телефона
    └── proot-distro login ubuntu  (контейнер Ubuntu, glibc)
        └── /root/quiz_bot_patched
            └── .venv/bin/python bot.py   ← сам бот
```

Почему так:
- **Termux** даёт Linux-окружение на Android, но на **musl** libc — многие Python-колёса
  (wheels) под него не собраны.
- **proot-distro Ubuntu** даёт настоящий **glibc** — туда ставятся обычные пакеты Python
  без боли.
- Бот запускается **внутри Ubuntu**, а Termux:Boot и sshd живут в **Termux**.

---

## 1. Подключение к телефону по ADB (Wi-Fi)

Удобно для первичной настройки без проводов. Телефон и компьютер — в одной Wi-Fi сети.

### Вариант A — Android 11+ (беспроводная отладка)
1. На телефоне: **Настройки → Для разработчиков → Беспроводная отладка → Вкл**.
2. Там же «Подключение с помощью кода» → увидите `IP:port` и 6-значный код.
3. На компьютере:
   ```bash
   adb pair <IP>:<порт_сопряжения>      # ввести 6-значный код
   adb connect <IP>:<порт_отладки>
   adb devices                          # должно показать device
   ```

### Вариант B — через USB один раз, дальше по Wi-Fi
1. Подключить телефон по USB, включить **Отладка по USB**.
2. ```bash
   adb tcpip 5555
   adb connect <IP_телефона>:5555
   ```
   (IP смотрится в Настройки → Wi-Fi → текущая сеть.)

> ADB нужен в основном для удобства/диагностики. Сам бот работает без ADB —
> после настройки SSH заходим по `ssh` (см. шаг 3).

---

## 2. Установка Termux (только F-Droid!)

⚠️ **НЕ ставьте Termux из Google Play** — версия там устарела и несовместима с
актуальными пакетами.

1. Установить **F-Droid**: https://f-droid.org → скачать APK → разрешить установку из
   неизвестных источников → установить.
2. В F-Droid установить:
   - **Termux**
   - **Termux:Boot** (для автозапуска, шаг 7)
   - (опц.) **Termux:API**
3. Открыть Termux и обновить пакеты:
   ```bash
   pkg update && pkg upgrade -y
   pkg install -y openssh proot-distro termux-services
   ```
4. Дать Termux доступ к хранилищу (на всякий случай):
   ```bash
   termux-setup-storage
   ```

> Все приложения Termux:* должны быть из **одного источника** (F-Droid),
> иначе они не «видят» друг друга (разные подписи).

---

## 3. Настройка SSH-сервера (порт 8022)

Termux'овый `sshd` слушает порт **8022** (не 22 — тот требует root).

1. Задать пароль для входа в Termux:
   ```bash
   passwd
   ```
2. Узнать имя пользователя Termux:
   ```bash
   whoami        # например u0_a123
   ```
3. Запустить sshd:
   ```bash
   sshd
   ```
4. Узнать IP телефона:
   ```bash
   ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1
   # или: ip addr show wlan0
   ```
5. С компьютера подключиться:
   ```bash
   ssh -p 8022 u0_a123@<IP_телефона>
   ```

### Вход по ключу (без пароля, рекомендуется)
На компьютере:
```bash
ssh-copy-id -p 8022 u0_a123@<IP_телефона>
# или вручную добавить свой ~/.ssh/id_*.pub в ~/.ssh/authorized_keys на телефоне
```

> Полезно: SSH заходит в **Termux**. Чтобы попасть в Ubuntu — после входа выполнить
> `proot-distro login ubuntu`.

---

## 4. Установка proot-distro + Ubuntu

В Termux:
```bash
pkg install -y proot-distro
proot-distro install ubuntu
```

Вход в Ubuntu:
```bash
proot-distro login ubuntu
```
Дальше вы внутри Ubuntu как `root`, домашняя папка — `/root`.

Базовая подготовка Ubuntu:
```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git curl build-essential
```

---

## 5. Установка Claude Code внутри Ubuntu

Claude Code — это CLI на Node.js. Ставится **внутри Ubuntu** (glibc), не в Termux.

```bash
# Внутри: proot-distro login ubuntu
apt install -y nodejs npm        # или nvm для свежей версии Node
node --version                   # нужен Node 18+

# Установка Claude Code
npm install -g @anthropic-ai/claude-code

# Запуск из папки проекта
cd /root/quiz_bot_patched
claude
```

Если `npm` ставит старый Node — поставить через nvm:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install --lts
npm install -g @anthropic-ai/claude-code
```

---

## 6. Решение типовых проблем

Это самые частые грабли на Android/proot. Запоминайте — повторяются всегда.

### 6.1. PostgreSQL зависает / `initdb` висит вечно → берём SQLite

На Android/PRoot `initdb` и запуск PostgreSQL **виснут навсегда** (проблемы с
fsync/shared memory под proot). Не пытайтесь поднять Postgres.

**Решение:** SQLite (файл) + при необходимости in-memory dict для кэша/локов.

- В коде использовать async-драйвер `aiosqlite`:
  ```python
  # config.py
  DB_FILE = "quiz_bot.db"
  db_url = f"sqlite+aiosqlite:///{DB_FILE}"
  ```
- Таблицы создавать на старте без alembic/initdb:
  ```python
  async with engine.begin() as conn:
      await conn.run_sync(Base.metadata.create_all)
  ```
- Redis (если был) заменить на in-memory словарь в том же процессе.

### 6.2. Rust-компиляция виснет/падает (pydantic-core, cryptography и т.п.) → `--only-binary`

Многие пакеты тянут Rust-сборку. На телефоне компиляция Rust **виснет на часы** или
падает по памяти.

**Решение:** запрещаем сборку из исходников — ставим только готовые бинарные колёса:
```bash
pip install --only-binary :all: -r requirements.txt
```
Если для какого-то пакета нет бинарного колеса под aarch64 — берём версию, для которой
оно есть (часто чуть старее), и фиксируем её в `requirements.txt`. Главное — **никогда
не давать pip собирать Rust на телефоне**.

### 6.3. Два разных Python (Termux musl vs Ubuntu glibc) → venv на `/usr/bin/python3`

Распространённая путаница: команда `python` может указывать на Termux'овый
интерпретатор (musl), под который колёс нет, и установка виснет/ломается.

**Правило:** бот и его venv должны жить на **glibc-Python из Ubuntu** —
это `/usr/bin/python3` внутри proot-distro.

```bash
# Внутри Ubuntu — проверить, что это glibc-питон:
/usr/bin/python3 --version
/usr/bin/python3 -c "import sysconfig; print(sysconfig.get_platform())"   # linux-aarch64

# Создавать venv ЯВНО от него:
cd /root/quiz_bot_patched
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install --only-binary :all: -r requirements.txt
```

⚠️ Всегда запускать бота через **`.venv/bin/python`**, а не через `python`/`python3`
из PATH — так гарантированно берётся правильный интерпретатор и зависимости venv.

---

## 7. Автозапуск через Termux:Boot

Чтобы бот сам поднимался при включении телефона.

1. Установить приложение **Termux:Boot** (из F-Droid, шаг 2) и **один раз открыть его** —
   иначе Android не даст ему стартовать при загрузке.
2. Отключить оптимизацию батареи для Termux (Настройки → Батарея → Termux → Без
   ограничений), иначе Android прибьёт процесс.
3. Создать скрипт автозапуска **в Termux** (не в Ubuntu!):
   ```bash
   mkdir -p ~/.termux/boot
   nano ~/.termux/boot/start.sh
   ```
4. Содержимое `~/.termux/boot/start.sh`:
   ```bash
   #!/data/data/com.termux/files/usr/bin/bash

   # Не даём телефону усыпить процессы
   termux-wake-lock

   # Запускаем SSH сервер
   sshd

   # Запускаем бота внутри Ubuntu с автоперезапуском
   proot-distro login ubuntu -- bash -c "
   while true; do
       cd /root/quiz_bot_patched
       .venv/bin/python bot.py >> /root/bot.log 2>&1
       echo 'Бот упал, перезапуск через 10 сек...' >> /root/bot.log
       sleep 10
   done
   " &
   ```
5. Сделать исполняемым:
   ```bash
   chmod +x ~/.termux/boot/start.sh
   ```

Что делает скрипт:
- `termux-wake-lock` — не даёт Android усыпить процессы.
- `sshd` — поднимает SSH (порт 8022), чтобы можно было зайти.
- цикл `while true` — **супервизор**: если `bot.py` упал, ждёт 10 сек и
  перезапускает. Логи пишутся в `/root/bot.log` (внутри Ubuntu).

---

## 8. Команда запуска бота (вручную)

```bash
cd /root/quiz_bot_patched && .venv/bin/python bot.py
```

Из Termux одной строкой (без интерактивного входа в Ubuntu):
```bash
proot-distro login ubuntu -- bash -c "cd /root/quiz_bot_patched && .venv/bin/python bot.py"
```

---

## 9. Управление запущенным ботом

> ⚠️ Telegram допускает **только один** активный поллер (`getUpdates`) на токен.
> Два запущенных экземпляра → ошибка **409 Conflict**. Поэтому: либо супервизор,
> либо ручной запуск — **не одновременно**.

### Посмотреть процессы
```bash
ps aux | grep "bot.py" | grep -v grep
# супервизор: bash -c "while true; ..."
# сам бот:    .venv/bin/python bot.py
```

### Перезапустить на новую версию кода (если работает супервизор из шага 7)
Достаточно убить только python — цикл сам поднимет обновлённый код через ~10 сек:
```bash
pkill -TERM -f "\.venv/bin/python bot.py"
```

### Полная остановка
```bash
pkill -f "while true"            # убить супервизор-цикл
pkill -TERM -f "\.venv/bin/python bot.py"   # убить сам бот
```

### Логи
```bash
tail -f /root/bot.log
# успешный старт: строка "Бот запущен ✅" и "Run polling for bot @..."
```

### Проверить таблицы SQLite
```bash
.venv/bin/python -c "import sqlite3; print([r[0] for r in sqlite3.connect('/root/quiz_bot_patched/quiz_bot.db').execute(\"select name from sqlite_master where type='table'\")])"
```

---

## 10. Чек-лист быстрого развёртывания на новом телефоне

1. [ ] F-Droid → Termux + Termux:Boot
2. [ ] `pkg update && pkg install -y openssh proot-distro`
3. [ ] `passwd`, `sshd`, узнать IP → проверить вход `ssh -p 8022 ...`
4. [ ] `proot-distro install ubuntu` → `proot-distro login ubuntu`
5. [ ] `apt install -y python3 python3-venv python3-pip git build-essential`
6. [ ] Скопировать проект в `/root/quiz_bot_patched`, заполнить `.env` (BOT_TOKEN)
7. [ ] `/usr/bin/python3 -m venv .venv` → `pip install --only-binary :all: -r requirements.txt`
8. [ ] БД = SQLite (никакого Postgres/initdb)
9. [ ] Проверить вручную: `cd /root/quiz_bot_patched && .venv/bin/python bot.py`
10. [ ] Открыть Termux:Boot один раз, создать `~/.termux/boot/start.sh`, `chmod +x`
11. [ ] Отключить оптимизацию батареи для Termux
12. [ ] Перезагрузить телефон → проверить `tail -f /root/bot.log`
