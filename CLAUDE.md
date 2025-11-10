# CLAUDE.md

Этот файл содержит руководство для Claude Code или CODEX при работе с кодом в этом репозитории.


---

## ВАЖНО: Обновление документации

**ОБЯЗАТЕЛЬНО НАДО ПЕРИОДИЧЕСКИ ОБНОВЛЯТЬ И ДОБАВЛЯТЬ ИНФОРМАЦИЮ В ЭТОТ ФАЙЛ И СЛЕДИТЬ ЗА ТЕМ, ЧТОБЫ ИНФОРМАЦИЯ НЕ ПРОТИВОРЕЧИЛА РЕАЛЬНОСТИ И ПРОЧИМ ДОКУМЕНТАЦИЯМ**

СЮДА ДОЛЖНА ДОБАВЛЯТЬСЯ ИНФОРМАЦИЯ ПО ПРОЕКТУ

---

## Общая суть проекта

Мы реализуем **Avito Tasker** - Telegram Mini App для заработка на выполнении простых задач в Avito.

**Суть:** Пользователи берут задачи, отправляют сообщения на Avito, загружают скриншоты и получают деньги после модерации.

**Технологии:**
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + @twa-dev/sdk
- Backend: FastAPI + asyncpg (НЕ SQLAlchemy!)
- Database: PostgreSQL 14+ (удаленный сервер)
- Deployment: Docker + Docker Compose + Nginx
- Принцип: KISS (Keep It Simple, Stupid)

---

## Главные правила разработки

### 1. ПЕРЕД НАЧАЛОМ КАЖДОГО БЛОКА

**ОБЯЗАТЕЛЬНО:**
- Открой и внимательно изучи соответствующую документацию:
  - [docs/RED.md](tg-app/docs/RED.md) - полное описание проекта, типы задач, роли
  - [docs/main.md](tg-app/docs/main.md) - детальная логика работы каждой страницы
  - [docs/tech-stack.md](tg-app/docs/tech-stack.md) - технические решения, credentials, env variables
  - [docs/plan.md](tg-app/docs/plan.md) - план реализации по блокам

- Продумай ИМЕННО ТУ информацию, которая пригодится для текущего блока
- Не делай предположений - проверяй в документации

**Если блок связан с UI/дизайном:**
- ОБЯЗАТЕЛЬНО смотри в папку `design/` на фотографии (screen.png)
- Доступные папки дизайна:
  - `design/main/` - главная страница
  - `design/money/` - модалка вывода средств (2 варианта: карта и СБП)
  - `design/one_task/` - страница деталей задачи
  - `design/referal/` - реферальная программа
  - `design/work_with_tasks/` - страница списка задач
- В каждой папке есть `code.html` с HTML+Tailwind кодом и `screen.png` со скриншотом

### 2. Технические требования

**База данных:**
- Используем ТОЛЬКО asyncpg (НЕ SQLAlchemy!)
- Прямые SQL-запросы без ORM
- Все запросы асинхронные через connection pool
- Все операции через глобальный экземпляр `db` из [app/db/database.py](tg-app/backend/app/db/database.py)

**Telegram WebApp:**
- Авторизация через initData validation (HMAC-SHA256)
- Передача initData в заголовке: `Authorization: tma {initData}`
- Реферальный код из start_param (Direct Link Mini App): `ref_TELEGRAM_ID`
- Формат реферальной ссылки: `https://t.me/{bot_username}/{app_short_name}?startapp=ref_{telegram_id}`
- Автоматическая регистрация пользователя при первом вызове `/api/auth/init`

**Ссылки на Avito:**
- НЕ открываем через `window.open()`
- Только КОПИРОВАНИЕ в буфер обмена через clipboard API
- Уведомление "Ссылка скопирована"

**Цены и инструкции:**
- Все приходят с бэкенда из конфига (НЕ хардкодить!)
- Простая задача: 50₽ (по умолчанию)
- Задача с номером: 150₽ (по умолчанию)
- Конфигурация в [app/utils/config.py](tg-app/backend/app/utils/config.py)

### 3. Важные особенности логики

**Баланс:**
- Два типа: `main_balance` + `referral_balance`
- Отображаем СУММУ обоих балансов
- При выводе НЕ вычитаем сразу (только после одобрения админом)
- Вычет происходит в SQL-запросе модерации (см. MODERATION.md)

**Задачи:**
- Лимит 10 активных задач одновременно
- Блокировка на 24 часа при взятии
- Автовозврат в пул если не отправлено за 24 часа
- Проверка автовозврата при КАЖДОМ запросе к `/api/tasks/*` (middleware)
- Middleware ОПТИМИЗИРОВАН: работает ТОЛЬКО на `/api/tasks/*` (не на health checks, static files)

**Скриншоты:**
- Минимум 1, максимум 5 на задачу
- Хранение локально на сервере в `/uploads/screenshots/` (НЕ в БД)
- Формат PNG, JPG, до 10 МБ
- Имя файла: `{assignment_id}_{timestamp}_{original_name}`
- Автоматическое удаление при автовозврате задачи

**Реферальная программа:**
- Одноуровневая (только прямые рефералы, без multi-level)
- 50% от КАЖДОГО заработка реферала
- Начисление автоматически при одобрении задачи реферала
- `referred_by` устанавливается один раз и не меняется (immutable)
- Защита от самореферала на уровне БД: `CHECK (referred_by != telegram_id)`

**Модерация:**
- Все задачи - вручную через БД
- Все выводы - вручную через БД
- SQL-инструкции в [backend/MODERATION.md](tg-app/backend/MODERATION.md)

### 4. Порядок реализации

**Frontend first:**
1. Сначала полностью реализуем frontend с моками
2. Тестируем все страницы и переходы
3. Потом создаем backend
4. В конце подключаем frontend к backend

### 5. Код-стайл и подход

- Минимум зависимостей
- Простые и понятные решения (KISS)
- Валидация данных на ОБОИХ уровнях (frontend + backend)
- Понятные сообщения об ошибках для пользователя
- Обработка всех edge cases
- НЕ использовать эмодзи в коде (только если явно требуется в UI)

### 6. Что НЕ делать

❌ НЕ использовать SQLAlchemy - только asyncpg
❌ НЕ создавать дополнительные файлы без необходимости
❌ НЕ хардкодить цены и настройки - только из конфига
❌ НЕ делать предположений - проверяй в документации
❌ НЕ упоминать "MVP" - это полноценная реализация
❌ НЕ открывать Avito ссылки - только копирование
❌ НЕ использовать wildcard CORS origins (CSRF уязвимость)

### 7. Тестирование

После каждого блока:
- Проверь, что все работает
- Проверь соответствие дизайну (если UI блок)
- Проверь соответствие логике из документации
- Проверь обработку ошибок

---

## Команды для разработки

### Разработка Frontend

```bash
cd tg-app/frontend

# Установка зависимостей
npm install

# Запуск dev-сервера (http://localhost:5173)
npm run dev

# Сборка для продакшена
npm run build

# Линтинг
npm run lint

# Превью продакшен-сборки
npm run preview
```

### Разработка Backend

```bash
cd tg-app/backend

# Создание и активация виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск dev-сервера (http://localhost:8000)
uvicorn app.main:app --reload --port 8000

# Инициализация схемы БД
python3 init_db.py

# Добавление тестовых задач
python3 add_test_tasks.py
```

### Развертывание через Docker

```bash
cd tg-app

# Сборка и запуск всех сервисов (frontend на :80, backend на :8000)
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка сервисов
docker-compose down

# Инициализация БД (только первый раз, внутри контейнера)
docker exec -it avito_tasker_backend python3 init_db.py
docker exec -it avito_tasker_backend python3 add_test_tasks.py
```

### Работа с базой данных

```bash
# Подключение к PostgreSQL
psql -h 81.30.105.134 -p 5416 -U admin -d avito_tasker

# Из Docker-контейнера
docker exec -it postgres_container psql -U admin -d avito_tasker
```

---

## Архитектура (важные детали)

### Паттерн работы с БД: asyncpg без ORM

Проект использует **прямые SQL-запросы** через asyncpg, БЕЗ SQLAlchemy или других ORM. Все операции с БД идут через глобальный экземпляр `db` из [app/db/database.py](tg-app/backend/app/db/database.py).

**Ключевые методы:**
- `db.fetch_one()` - SELECT одной строки, возвращает dict или None
- `db.fetch_all()` - SELECT нескольких строк, возвращает list[dict]
- `db.fetch_val()` - SELECT одного скалярного значения (например, COUNT)
- `db.execute()` - INSERT/UPDATE/DELETE
- `db.transaction()` - Context manager для атомарных операций

**Пример транзакции:**
```python
async with db.transaction() as conn:
    await conn.execute(
        "UPDATE users SET main_balance = main_balance + $1 WHERE telegram_id = $2",
        amount, user_id
    )
    await conn.execute(
        "INSERT INTO referral_earnings (...) VALUES (...)",
        ...
    )
```

**ВАЖНО:** Внутри транзакций используй `conn.execute()`, НЕ `db.execute()`.

### Поток аутентификации Telegram

1. Пользователь открывает Mini App в Telegram
2. Telegram предоставляет `initData` (подписанную строку) через WebApp SDK
3. Frontend отправляет заголовок `Authorization: tma {initData}`
4. Backend проверяет подпись через HMAC-SHA256 с секретным ключом бота
5. Пользователь автоматически регистрируется при первом вызове `/api/auth/init`
6. Dependency `get_current_user()` извлекает telegram_id, username, first_name, start_param

**Критично:** Ссылки на Avito нужно **копировать в буфер обмена**, НИКОГДА не открывать через `window.open()` (бизнес-требование).

### Жизненный цикл задачи и механизм автовозврата

Задачи имеют сложный жизненный цикл с автоматическим истечением:

1. **Назначение:** Пользователь берет задачу через `/api/tasks/{id}/assign`
   - Задача помечается `is_available = FALSE`
   - Создается assignment с дедлайном 24 часа
   - У пользователя может быть максимум 10 активных задач (проверка в API)

2. **Отправка:** Пользователь загружает скриншоты и отправляет через `/api/tasks/{id}/submit`
   - Скриншоты сохраняются в `/uploads/screenshots/` на диске
   - Статус assignment меняется на `submitted`

3. **Middleware автовозврата:** Запускается при КАЖДОМ запросе к `/api/tasks/*`
   - Находит просроченные assignments (`status='assigned' AND deadline < NOW()`)
   - Возвращает задачу в пул (`is_available = TRUE`)
   - Удаляет assignment и файлы скриншотов
   - Использует `SELECT FOR UPDATE SKIP LOCKED` для предотвращения race conditions

4. **Модерация админом:** Вручную через SQL (см. [backend/MODERATION.md](tg-app/backend/MODERATION.md))
   - Одобрение: Начисляет баланс пользователю, запускает реферальную комиссию, возвращает задачу в пул
   - Отклонение: Возвращает задачу в пул, скриншоты остаются для проверки

**Важно:** Middleware автовозврата ОПТИМИЗИРОВАН - работает только на `/api/tasks/*` endpoints (не на health checks, static files и т.д.) для снижения нагрузки на БД.

### Архитектура реферальной системы

Одноуровневая реферальная система (только прямые рефералы, без мультиуровня):

1. **Регистрация:** Пользователь B кликает на реферальную ссылку: `t.me/bot/app?startapp=ref_{TELEGRAM_ID_A}`
   - Формат Direct Link Mini App: `https://t.me/{bot_username}/{app_short_name}?startapp=ref_{telegram_id}`
   - Пример: `https://t.me/avito_tasker_bot/avitotasker?startapp=ref_123456789`
2. Telegram передает `start_param=ref_{TELEGRAM_ID_A}` в `initData` при первой загрузке WebApp
3. Frontend вызывает `/api/auth/init` с start_param в заголовке Authorization
4. Backend парсит start_param и устанавливает у User B значение `referred_by = TELEGRAM_ID_A` (неизменяемое)

5. **Триггер комиссии:** Когда админ одобряет задачу User B:
   - User B получает оплату задачи в `main_balance`
   - User A получает 50% комиссии в `referral_balance` (автоматически в SQL одобрения)
   - Запись вставляется в таблицу `referral_earnings`

**Ограничения БД:**
- Самореферал предотвращен на уровне БД: `CHECK (referred_by != telegram_id)`
- `referred_by` неизменяемо после первой установки

### Система балансов

Два типа баланса для каждого пользователя:
- `main_balance` - Заработано за выполнение задач
- `referral_balance` - Заработано с реферальных комиссий

**Отображение:** Frontend показывает сумму обоих балансов

**Вывод средств:** Баланс НЕ списывается сразу при запросе на вывод. Списание происходит ТОЛЬКО когда админ одобряет вывод через SQL (см. MODERATION.md).

### Frontend роутинг и страницы

React Router v6 с 4 основными страницами:

- [Home.tsx](tg-app/frontend/src/pages/Home.tsx) - Отображение баланса, модалка вывода, быстрая статистика
- [TasksPage.tsx](tg-app/frontend/src/pages/TasksPage.tsx) - Список активных задач + запрос новой задачи
- [TaskDetailPage.tsx](tg-app/frontend/src/pages/TaskDetailPage.tsx) - Инструкции задачи, загрузка скриншотов, отправка
- [ReferralsPage.tsx](tg-app/frontend/src/pages/ReferralsPage.tsx) - Реферальная ссылка, статистика, список заработков

**Управление состоянием:** Нет Redux/Zustand. API вызовы через Axios в [services/api.ts](tg-app/frontend/src/services/api.ts). Локальное состояние через React hooks.

### Управление конфигурацией

Backend использует централизованную систему конфигурации в [app/utils/config.py](tg-app/backend/app/utils/config.py):

```python
# Telegram Configuration
config.TELEGRAM_BOT_TOKEN  # Токен бота из BotFather
config.TELEGRAM_BOT_USERNAME  # Username бота (например: avito_tasker_bot)
config.TELEGRAM_APP_SHORT_NAME  # Короткое имя Mini App из BotFather (по умолчанию: avitotasker)

# Pricing & Limits
config.SIMPLE_TASK_PRICE  # По умолчанию: 50 рублей
config.PHONE_TASK_PRICE   # По умолчанию: 150 рублей
config.REFERRAL_COMMISSION  # По умолчанию: 0.5 (50%)
config.MIN_WITHDRAWAL  # По умолчанию: 100 рублей
config.MAX_ACTIVE_TASKS  # По умолчанию: 10
config.TASK_LOCK_HOURS  # По умолчанию: 24
```

Frontend получает конфигурацию через endpoint `/api/config`. **НИКОГДА не хардкодить цены или лимиты** - всегда используй значения из конфига.

### Поток загрузки скриншотов

1. Frontend: Пользователь выбирает 1-5 изображений (PNG/JPG, макс 10MB каждое)
2. POST `/api/screenshots/upload` с `multipart/form-data`
   - Обязательные поля: `assignment_id`, `file`
3. Backend: Валидирует тип файла, размер, сохраняет в `UPLOAD_DIR/screenshots/`
   - Имя файла: `{assignment_id}_{timestamp}_{original_name}`
4. Запись вставляется в таблицу `screenshots` с `file_path`
5. Frontend получает через `/static/screenshots/{filename}`

**Очистка:** Middleware автовозврата удаляет файлы скриншотов при истечении задач.

---

## Важные технические детали

### Выравнивание схемы БД

TypeScript типы в [frontend/src/types/index.ts](tg-app/frontend/src/types/index.ts) выровнены со схемой PostgreSQL в [backend/schema.sql](tg-app/backend/schema.sql). При изменении схемы БД обновляй оба файла.

### Конфигурация CORS

Backend CORS **зависит от окружения** (см. [app/main.py](tg-app/backend/app/main.py:61-85)):

- **Development:** Разрешает localhost:5173 + regex для localtunnel/Cloudflare tunnel
- **Production:** Разрешает ТОЛЬКО `https://web.telegram.org` (origin Telegram Mini Apps)

**Критично:** НИКОГДА не используй wildcard CORS origins (уязвимость CSRF).

### Паттерн обработки ошибок

Backend endpoints должны ловить исключения и возвращать соответствующие HTTP коды:
- 400 - Bad request (ошибки валидации)
- 401 - Unauthorized (отсутствует/невалидный initData)
- 404 - Not found
- 409 - Conflict (например, превышен лимит задач, дублирование assignment)
- 500 - Internal server error

Frontend показывает понятные пользователю сообщения об ошибках через Toast уведомления ([components/ui/Toast.tsx](tg-app/frontend/src/components/ui/Toast.tsx)).

### Логирование и приватность

Backend использует логирование с соблюдением GDPR:
- ID пользователей хешируются в логах: `hash_user_id(telegram_id)` (см. [dependencies/auth.py](tg-app/backend/app/dependencies/auth.py:19-21))
- Чувствительные данные (номера телефонов, реквизиты карт) НИКОГДА не логируются

### Архитектура развертывания

Docker Compose setup:
- Frontend контейнер: React build обслуживается Nginx на порту 80
- Backend контейнер: FastAPI через uvicorn на порту 8000
- Nginx выступает как reverse proxy: `/api/*` → backend, `/*` → frontend
- PostgreSQL внешний (удаленный сервер, не в Docker)

**Требуется HTTPS:** Telegram Mini Apps работают только через HTTPS. Используй Cloudflare Tunnel или Let's Encrypt для продакшена.

---

## Тестирование и разработка

### Тестирование Telegram Mini Apps

Нельзя тестировать напрямую в браузере - требуется контекст Telegram:

**Вариант 1:** Localtunnel для быстрого тестирования
```bash
npx localtunnel --port 5173
```

**Вариант 2:** Cloudflare Tunnel (см. [start-with-cloudflare.sh](tg-app/start-with-cloudflare.sh))
```bash
./start-with-cloudflare.sh
```

Используй сгенерированный URL в настройках Mini App в BotFather.

### Документация API

FastAPI автоматически генерирует документацию:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Операции администратора

Вся модерация выполняется через SQL-запросы, документированные в [backend/MODERATION.md](tg-app/backend/MODERATION.md):
- Одобрение/отклонение отправленных задач (автоматически запускает реферальную комиссию)
- Одобрение/отклонение запросов на вывод (списывает баланс)
- Просмотр ожидающих задач/выводов
- Статистика пользователей

---

## Примеры правильного подхода

**✅ Правильно:**
1. Читаю документацию для блока "Главная страница"
2. Смотрю `design/main/screen.png` для понимания UI
3. Изучаю логику из `docs/main.md`
4. Реализую с учетом ВСЕЙ информации
5. Тестирую

**❌ Неправильно:**
1. Сразу начинаю писать код
2. Делаю предположения о логике
3. Не смотрю на дизайн
4. Хардкожу значения

---

## Принципы проекта

**KISS (Keep It Simple, Stupid):**
- Минимум зависимостей
- Прямые SQL-запросы (без сложности ORM)
- Простая аутентификация (валидация Telegram initData)
- Без сложного управления состоянием (только React hooks)

**Валидация данных:**
- Frontend: Валидация форм перед API вызовами
- Backend: Pydantic модели + SQL constraints
- Database: CHECK constraints, foreign keys, unique indexes

**Организация файлов:**
- Backend: Плоская структура в `app/` (api, db, dependencies, utils)
- Frontend: Компоненты по фичам (pages, components/ui, components/tasks и т.д.)
- Документация и дизайн-файлы отдельно от кода

---

**Помни: Простота, документация и KISS - наши главные принципы!**
