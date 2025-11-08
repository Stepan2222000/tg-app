# Технический стек проекта

## Frontend

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Telegram Integration:** @twa-dev/sdk
- **HTTP Client:** Axios / Fetch API
- **Routing:** React Router v6

## Backend

- **Framework:** FastAPI (Python)
- **Database Driver:** **asyncpg** (NOT SQLAlchemy)
  - Асинхронный драйвер для PostgreSQL
  - Прямые SQL-запросы без ORM
  - Высокая производительность
- **Authentication:** Telegram initData validation
- **File Upload:** Multipart form data для скриншотов

## Database

- **СУБД:** PostgreSQL
- **Расположение:** Удаленный сервер
- **Credentials:**
  - Host: `81.30.105.134`
  - Port: `5416`
  - Database: `avito_tasker`
  - Username: `admin`
  - Password: `Password123`

## File Storage

- **Screenshots:** Локальное хранение на сервере
- **Path:** `/backend/uploads/screenshots/`
- **Format:** PNG, JPG (до 5 файлов на задачу)
- **Max Size:** 10 MB на файл

## Ключевые технические решения

### 1. База данных
- Используем **asyncpg** для прямой работы с PostgreSQL
- Все запросы асинхронные
- Пулинг соединений для оптимизации
- Транзакции для критичных операций (начисления баланса, модерация)

### 2. Авторизация
- Telegram передает initData при запуске Mini App
- Backend валидирует подпись через секретный ключ бота
- Извлекаем `telegram_id`, `username`, `first_name`
- Автоматическая регистрация при первом входе

### 3. Реферальная система
- Формат ссылки (Direct Link Mini App): `https://t.me/bot/app_short_name?startapp=ref_TELEGRAM_ID`
- Параметр `startapp=ref_TELEGRAM_ID` передается в `initData.start_param`
- При первой авторизации сохраняется связь реферер-реферал
- Начисления происходят автоматически при одобрении задачи реферала

### 4. Автовозврат задач
- Проверка при каждом API запросе
- Если `task.deadline < current_time` и статус = "assigned" → возврат в пул
- Удаление загруженных скриншотов при автовозврате

### 5. Модерация
- **Задачи:** Вручную добавляются администратором в БД
- **Выполнение:** Вручную проверяется администратором в БД
- **Вывод средств:** Вручную обрабатывается администратором

## Структура проекта

```
tg-app/
├── docs/               # Документация
├── design/             # UI/UX макеты (HTML + PNG)
├── frontend/           # React приложение
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/   # API клиент
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
└── backend/            # FastAPI приложение
    ├── app/
    │   ├── api/        # Роуты
    │   ├── db/         # asyncpg connection pool
    │   ├── models/     # TypedDict для данных
    │   └── utils/      # Валидация, хелперы
    ├── uploads/
    │   └── screenshots/
    ├── requirements.txt
    └── main.py
```

## Тестовые данные

### Avito URLs для тестирования:

1. **Простая задача #1**
   - URL: `https://www.avito.ru/brands/82268a835092c9677ebe7278a13a866d`
   - Текст: "добрый вечер, я диспетчер"

2. **Простая задача #2**
   - URL: `https://www.avito.ru/brands/fc6076e06d696884d07f26a4828dc6e3`
   - Текст: "друг мой, здравствуй"

3. **Задача с номером #1**
   - URL: `https://www.avito.ru/brands/94b135edb89761f77fdfab2f5a82a345`
   - Текст: "привет, отправь номер"

4. **Задача с номером #2**
   - URL: `https://www.avito.ru/brands/16f6fd2b4f11b60a3ec2ab2084d34bf6`
   - Текст: "hello, you good boy"

## Bot Credentials

- **Token:** `8210464425:AAE67y14gEU_nvLfvDrIqpC7SMiyas9SsZk`
- **Username:** `@avito_tasker_bot`

## Environment Variables

### Backend (.env)
```
DATABASE_HOST=81.30.105.134
DATABASE_PORT=5416
DATABASE_NAME=avito_tasker
DATABASE_USER=admin
DATABASE_PASSWORD=Password123

TELEGRAM_BOT_TOKEN=8210464425:AAE67y14gEU_nvLfvDrIqpC7SMiyas9SsZk

UPLOAD_DIR=./uploads/screenshots
MAX_FILE_SIZE=10485760

# Config
SIMPLE_TASK_PRICE=50
PHONE_TASK_PRICE=150
REFERRAL_COMMISSION=0.5
MIN_WITHDRAWAL=100
MAX_ACTIVE_TASKS=10
TASK_LOCK_HOURS=24
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_BOT_USERNAME=avito_tasker_bot
```

## Принципы разработки

- **KISS (Keep It Simple, Stupid)** - максимальная простота архитектуры
- Прямые SQL-запросы вместо ORM для прозрачности
- Минимум зависимостей
- Четкое разделение frontend/backend
- Валидация данных на обоих уровнях
- Обработка ошибок с понятными сообщениями пользователю
