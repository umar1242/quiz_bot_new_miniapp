# Quiz Bot (Mini App Edition)

Telegram-бот и набор Mini Apps для проведения тестирований, выдачи сертификатов (Milliy sertifikat - Biologiya) и других интерактивных материалов.

## Структура проекта
- `bot.py` — Точка входа для aiogram бота. Отвечает за прием команд (например, `/start`, `/cert`) и показ меню Mini App.
- `webapp/server.py` — AIOHTTP сервер, который выступает API-бэкендом для Mini Apps и раздает статические файлы.
- `webapp/frontend-cert/` — React/Vite фронтенд для создания и прохождения сертификационных тестов (Cert-App).
- `webapp/static/cert-app/` — Собранный билд фронтенда для сертификатов (генерируется с помощью `npm run build` из папки `frontend-cert`).
- `services/` — Бизнес-логика, работа с базой данных (SQLAlchemy) и обработка различных типов вопросов (включая Y1, Y2).
- `models/` — Модели базы данных SQLAlchemy.

## Особенности
- **Интеграция с Telegram Web App:** Позволяет открывать красивые интерфейсы (React) прямо в мессенджере.
- **Сложные типы вопросов:** Поддерживает вопросы типа Y2 (33–35), где несколько подвопросов имеют общие варианты ответа.
- **Туннелирование (Serveo):** Бот автоматически поднимает SSH-туннель (Serveo) при локальном запуске, чтобы Telegram мог достучаться до Web App.

## Запуск
Бот и веб-сервер запускаются одним скриптом:
```bash
# Установите зависимости
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Запустите бота
python bot.py
```

## Сборка фронтенда (React)
Если вы вносите изменения в React-код (например, в `webapp/frontend-cert`), необходимо пересобрать статику:
```bash
cd webapp/frontend-cert
npm install
npm run build
```
После этого перезапустите `bot.py`.
