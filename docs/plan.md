# План реализации Avito Tasker

## ЧАСТЬ 1: FRONTEND (React + TypeScript + Vite)

### Блок 1: Инициализация и базовая настройка
1. Создать React проект через Vite с TypeScript
2. Установить зависимости: react-router-dom, @twa-dev/sdk, axios, Tailwind CSS
3. Настроить Tailwind config с цветами из дизайна (primary, background, card, text)
4. Создать .env файл (VITE_API_URL, VITE_BOT_USERNAME)

### Блок 2: TypeScript типы и сервисы
5. Создать типы: User, Task, TaskAssignment, Withdrawal, Referral, Config
6. Создать структуру папок: components, pages, services, hooks, utils, types
7. Настроить Telegram WebApp SDK: инициализация, получение initData, темы
8. Создать API сервис с axios: interceptor для initData, типизированные методы

### Блок 3: Утилиты и хуки
9. Создать утилиты форматирования: валюта, дата, телефон, валидация карты/телефона
10. Создать хук useCountdown: таймер обратного отсчета с процентами для прогресс-бара
11. Создать хук useNotification: toast-уведомления

### Блок 4: UI компоненты
12. Создать базовые компоненты: Button, Input, Modal, Toast

### Блок 5: Главная страница (/)
13. Создать Home страницу: баланс (main + referral), кнопки навигации, блок "Как это работает?"
14. Создать WithdrawalModal: сумма, toggle карта/СБП, динамические поля, валидация, отправка заявки

### Блок 6: Страница задач (/tasks)
15. Создать Tasks страницу: круговой индикатор лимита 7/10, кнопки типов задач с ценами, модалка подтверждения
16. Создать ActiveTaskCard: ID, тип, таймер, прогресс-бар с цветами (зеленый/желтый/красный)

### Блок 7: Страница деталей задачи (/tasks/:id)
17. Создать TaskDetail страницу: шапка, таймер, вознаграждение, инструкции, кнопка копирования ссылки Avito
18. Добавить блок текста для отправки с копированием
19. Добавить поле номера телефона (только для type='phone')
20. Создать ScreenshotUploader: сетка 3 колонки, до 5 файлов, превью, удаление
21. Footer с кнопками: "Отправить на модерацию" (валидация скриншотов/номера), "Отказаться"

### Блок 8: Страница реферальной программы (/referrals)
22. Создать Referrals страницу: ссылка с копированием, статистика (друзья + заработок)
23. Список рефералов с детализацией (ID, задачи, заработок) или empty state
24. Модалка помощи: объяснение работы программы (50% комиссия)

### Блок 9: Routing и финальная сборка
25. Настроить React Router: /, /tasks, /tasks/:id, /referrals
26. Добавить Layout с обработкой тем и toast-контейнером
27. Инициализация Telegram WebApp и авторизация в App.tsx
28. Тестирование Frontend с моковыми данными

---

## ЧАСТЬ 2: BACKEND (FastAPI + asyncpg)

### Блок 10: Инициализация проекта
29. Создать структуру: app/{api,db,models,utils}, uploads/screenshots
30. Создать requirements.txt: fastapi, uvicorn, asyncpg, python-multipart, python-dotenv, aiofiles
31. Создать .env с настройками БД, бота, цен, лимитов

### Блок 11: База данных
32. Создать schema.sql: таблицы users, tasks, task_assignments, screenshots, withdrawals, referral_earnings
33. Создать database.py: asyncpg pool, функции execute, fetch_one, fetch_all
34. Создать скрипт init_db.py для создания таблиц

### Блок 12: Авторизация
35. Создать telegram.py: функция validate_init_data через HMAC-SHA256
36. Создать auth middleware в main.py: проверка Authorization заголовка, валидация initData, сохранение user в request.state

### Блок 13: API - Конфигурация и пользователи
37. GET /api/config: цены задач, инструкции, настройки (min_withdrawal, max_active_tasks)
38. POST /api/auth/init: проверка/создание пользователя, обработка реферального кода
39. GET /api/user/me: данные пользователя и балансы

### Блок 14: API - Задачи
40. Middleware автовозврата: проверка просроченных задач при каждом запросе, возврат в пул, удаление скриншотов
41. GET /api/tasks/available?type: случайная доступная задача
42. GET /api/tasks/active: список активных задач пользователя
43. GET /api/tasks/:id: детали задачи с проверкой владения
44. POST /api/tasks/:task_id/assign: взятие задачи с проверкой лимита, создание assignment, deadline +24 часа
45. POST /api/tasks/:assignment_id/submit: отправка на модерацию с валидацией скриншотов/номера
46. POST /api/tasks/:assignment_id/cancel: отказ от задачи, удаление скриншотов, возврат в пул

### Блок 15: API - Скриншоты
47. POST /api/screenshots/upload: multipart загрузка, валидация типа/размера, лимит 5 файлов, сохранение в БД и на диск
48. DELETE /api/screenshots/:id: удаление с проверкой владения, удаление файла и записи в БД

### Блок 16: API - Вывод средств
49. POST /api/withdrawals: создание заявки с валидацией минимума и баланса
50. GET /api/withdrawals/history: история выводов с парсингом JSON details

### Блок 17: API - Реферальная программа
51. GET /api/referrals/link: генерация ссылки https://t.me/bot?start=ref_TELEGRAM_ID
52. GET /api/referrals/stats: количество рефералов и общий заработок
53. GET /api/referrals/list: список рефералов с детализацией задач и заработка, сортировка по убыванию

### Блок 18: Модерация и тестовые данные
54. Создать MODERATION.md: SQL-инструкции для одобрения/отклонения задач, одобрения выводов, начисления реферальных комиссий
55. Создать add_test_tasks.py: скрипт для добавления 4 тестовых задач (2 simple, 2 phone) из tech-stack.md
56. Тестирование Backend: проверка всех эндпоинтов, автовозврата, реферальных начислений

---

## ЧАСТЬ 3: ИНТЕГРАЦИЯ И ЗАПУСК

### Блок 19: Финальная интеграция
57. Подключить Frontend к Backend: заменить моки на реальные запросы
58. Тестирование полных потоков: регистрация с рефералом → взятие задачи → загрузка скриншотов → отправка → вывод средств
59. Настроить Telegram Bot (@BotFather): setmenubutton с URL Mini App
60. Финальное тестирование в Telegram на мобильном: все функции, темная/светлая тема
61. Создать README.md: инструкции по установке и запуску frontend/backend

---

**Все функции реализуются полностью по принципу KISS**
