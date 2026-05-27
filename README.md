# Лабораторная работа №5

## Кеширование данных и управление сессиями с использованием Redis

Проект является продолжением лабораторных работ №2, №3 и №4.

В рамках лабораторной работы №5 в существующее REST API на **FastAPI** добавлена интеграция с **Redis** для кеширования часто запрашиваемых данных и управления access-сессиями через хранение JTI access-токенов.

Redis используется для:

- кеширования списка пользовательских ресурсов `GET /items`;
- кеширования профиля пользователя `GET /auth/whoami`;
- хранения JTI access-токенов с TTL;
- мгновенной инвалидации access-токена при logout;
- инвалидации кеша при изменении данных.

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Стек технологий](#стек-технологий)
- [Что реализовано в лабораторной №5](#что-реализовано-в-лабораторной-5)
- [Структура проекта](#структура-проекта)
- [Переменные окружения](#переменные-окружения)
- [Запуск через Docker](#запуск-через-docker)
- [Redis](#redis)
- [Кеширование items](#кеширование-items)
- [Инвалидация кеша items](#инвалидация-кеша-items)
- [Кеширование профиля пользователя](#кеширование-профиля-пользователя)
- [Управление access token через JTI](#управление-access-token-через-jti)
- [Logout через Redis](#logout-через-redis)
- [API endpoints](#api-endpoints)
- [Проверка через Swagger UI](#проверка-через-swagger-ui)
- [Проверка Redis через CLI](#проверка-redis-через-cli)
- [Swagger / OpenAPI документация](#swagger--openapi-документация)
- [Production-режим](#production-режим)
- [Yandex OAuth](#yandex-oauth)
- [Безопасность](#безопасность)
- [Миграции базы данных](#миграции-базы-данных)
- [Проверка данных в БД](#проверка-данных-в-бд)
- [Контрольные вопросы](#контрольные-вопросы)
- [Финальная проверка перед сдачей](#финальная-проверка-перед-сдачей)
- [Автор](#автор)

---

## Описание проекта

REST API реализовано на **FastAPI** с использованием **PostgreSQL**, **SQLAlchemy**, **Alembic**, **Redis** и **Docker Compose**.

Проект наследует функциональность предыдущих лабораторных работ:

- CRUD API для ресурса `items`;
- пагинация;
- Soft Delete;
- регистрация пользователей;
- вход по email и паролю;
- JWT Access Token и Refresh Token;
- передача токенов через `HttpOnly` cookies;
- хранение хешей токенов в базе данных;
- выход из текущей сессии;
- выход из всех сессий;
- OAuth-вход через **Yandex ID**;
- восстановление пароля через reset token;
- автоматическая документация API через OpenAPI / Swagger UI.

В лабораторной работе №5 к проекту добавлен Redis.

Основная идея работы:

```text
Client → FastAPI → Redis → PostgreSQL
```

Для часто читаемых данных приложение сначала проверяет Redis.

Если данные есть в кеше, они возвращаются сразу.

Если данных нет, приложение обращается к PostgreSQL, сохраняет результат в Redis и возвращает ответ клиенту.

---

## Стек технологий

| Технология | Назначение |
| --- | --- |
| Python 3.11 | Язык программирования |
| FastAPI | Web API framework |
| PostgreSQL 16 | Основная база данных |
| Redis 7 | Кеш и хранение JTI access-токенов |
| SQLAlchemy | ORM |
| Alembic | Миграции базы данных |
| Pydantic | DTO, схемы данных и валидация |
| Uvicorn | ASGI-сервер |
| Docker / Docker Compose | Контейнеризация |
| python-jose | Работа с JWT |
| passlib / bcrypt | Хеширование паролей |
| redis-py | Клиент Redis для Python |
| httpx | HTTP-запросы к OAuth-провайдеру |
| OpenAPI / Swagger UI | Документация API |
| Yandex ID | OAuth 2.0 провайдер |

---

## Что реализовано в лабораторной №5

| Требование | Реализация |
| --- | --- |
| Redis добавлен в Docker Compose | ✅ Сервис `redis` на базе `redis:7-alpine` |
| Redis защищен паролем | ✅ Используется `REDIS_PASSWORD` |
| Настройки Redis вынесены в `.env` | ✅ `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `CACHE_TTL_DEFAULT` |
| Отдельный слой кеширования | ✅ `app/cache/cache_service.py` |
| Методы кеш-сервиса | ✅ `get`, `set`, `delete`, `delete_by_pattern` |
| TTL для ключей | ✅ Все ключи создаются с временем жизни |
| Кеширование `GET /items` | ✅ С учетом `owner_id`, `limit`, `offset` |
| Инвалидация items-кеша | ✅ При `POST`, `PUT`, `PATCH`, `DELETE` |
| Кеширование `GET /auth/whoami` | ✅ Профиль пользователя сохраняется в Redis |
| Инвалидация профиля | ✅ При logout профиль удаляется из Redis |
| JTI access-токена | ✅ Access token содержит уникальный `jti` |
| Хранение JTI в Redis | ✅ `wp:auth:user:{user_id}:access:{jti}` |
| Проверка JTI при авторизации | ✅ Если JTI удален из Redis, access token недействителен |
| Logout через Redis | ✅ При logout JTI удаляется из Redis |
| Безопасность данных | ✅ Пароли и полные токены не хранятся в Redis |

---

## Структура проекта

```text
app/
├── auth/
│   ├── dependencies.py      # получение текущего пользователя и проверка access token + Redis JTI
│   ├── oauth_yandex.py      # Yandex OAuth flow
│   ├── router.py            # auth endpoints + OpenAPI metadata
│   ├── security.py          # JWT, password hash, token hash, JTI
│   └── service.py           # auth business logic + Redis JTI/profile cache
│
├── cache/
│   ├── __init__.py
│   └── cache_service.py     # общий сервис работы с Redis
│
├── models/
│   ├── auth_token.py
│   ├── item.py
│   ├── password_reset_token.py
│   └── user.py
│
├── routers/
│   └── item_router.py       # items CRUD endpoints
│
├── schemas/
│   ├── auth.py
│   ├── item.py
│   └── user.py
│
├── services/
│   └── item_service.py      # бизнес-логика items + кеширование Redis
│
├── config.py
├── database.py
└── main.py
```

---

## Переменные окружения

Создайте файл `.env` на основе `.env.example`.

```bash
cp .env.example .env
```

Для Windows PowerShell:

```powershell
copy .env.example .env
```

Пример `.env.example`:

```env
APP_ENV=development

DB_USER=student
DB_PASSWORD=student
DB_NAME=lab_db
DB_HOST=postgres
DB_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=change_me_redis_password
CACHE_TTL_DEFAULT=300

JWT_ACCESS_SECRET=change_me_access_secret
JWT_REFRESH_SECRET=change_me_refresh_secret
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:8000/auth/oauth/yandex/callback
CLIENT_URL=http://localhost:8000/api/docs
```

> Файл `.env` не должен попадать в GitHub, так как содержит секреты, пароли и OAuth credentials.

---

## Запуск через Docker

### 1. Клонировать репозиторий

```bash
git clone https://github.com/quazerbee/lab_2.git
cd lab_2
git checkout lab5-redis
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Для Windows PowerShell:

```powershell
copy .env.example .env
```

### 3. Запустить контейнеры

```bash
docker compose up --build -d
```

### 4. Проверить контейнеры

```bash
docker compose ps
```

Должны быть запущены контейнеры:

```text
lab_app
lab_postgres
lab_redis
```

Пример успешного состояния:

```text
lab_postgres   Up   healthy
lab_redis      Up   healthy
lab_app        Up
```

### 5. Применить миграции

```bash
docker exec -it lab_app python -m alembic upgrade head
```

### 6. Проверить работу API

Откройте в браузере:

```text
http://localhost:8000/
```

Ожидаемый ответ:

```json
{
  "message": "API is working"
}
```

---

## Redis

В `docker-compose.yml` добавлен отдельный сервис Redis:

```yaml
redis:
  image: redis:7-alpine
  container_name: lab_redis
  restart: always
  ports:
    - "6379:6379"
  command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

Redis используется как in-memory key-value хранилище.

В проекте он применяется для:

- кеширования списков `items`;
- кеширования профиля пользователя;
- хранения JTI access-токенов;
- инвалидации сессий при logout.

Все ключи имеют префикс `wp:`.

Основные форматы ключей:

```text
wp:items:list:user:{user_id}:limit:{limit}:offset:{offset}
wp:items:item:{item_id}
wp:users:profile:{user_id}
wp:auth:user:{user_id}:access:{jti}
```

---

## Кеширование items

Для endpoint:

```text
GET /items?limit=10&offset=0
```

используется стратегия **Cache-Aside**.

Логика работы:

```text
1. Пользователь вызывает GET /items.
2. Приложение формирует Redis-ключ с user_id, limit и offset.
3. Приложение проверяет наличие данных в Redis.
4. Если данные есть, они возвращаются из кеша.
5. Если данных нет, приложение делает запрос в PostgreSQL.
6. Результат сохраняется в Redis с TTL.
7. Ответ возвращается пользователю.
```

Пример ключа:

```text
wp:items:list:user:4:limit:10:offset:0
```

Параметры `limit` и `offset` включены в ключ, потому что разные страницы списка должны кешироваться отдельно.

Примеры разных ключей:

```text
wp:items:list:user:4:limit:10:offset:0
wp:items:list:user:4:limit:10:offset:10
wp:items:list:user:4:limit:100:offset:0
wp:items:list:user:4:limit:100:offset:10
```

---

## Инвалидация кеша items

Кеш списка items удаляется при любых операциях записи:

| Метод | URI | Действие с кешем |
| --- | --- | --- |
| GET | `/items` | Чтение из кеша или запись в кеш |
| POST | `/items` | Удаление кеша списков пользователя |
| PUT | `/items/{item_id}` | Удаление кеша списков и конкретного item |
| PATCH | `/items/{item_id}` | Удаление кеша списков и конкретного item |
| DELETE | `/items/{item_id}` | Удаление кеша списков и конкретного item |

При изменении данных удаляются ключи по шаблону:

```text
wp:items:list:user:{user_id}:*
```

Это нужно, чтобы пользователь не получил устаревший список после создания, изменения или удаления ресурса.

---

## Кеширование профиля пользователя

Для endpoint:

```text
GET /auth/whoami
```

реализовано кеширование профиля пользователя.

Ключ:

```text
wp:users:profile:{user_id}
```

Пример:

```text
wp:users:profile:4
```

В Redis сохраняются только безопасные данные:

```json
{
  "id": 4,
  "email": "user@example.com"
}
```

В кеше не хранятся:

- пароль;
- хеш пароля;
- соль пароля;
- access token;
- refresh token;
- хеши токенов;
- reset token.

При logout кеш профиля удаляется.

---

## Управление access token через JTI

В access token добавлен уникальный идентификатор `jti`.

Пример payload access-токена:

```json
{
  "sub": "4",
  "email": "user@example.com",
  "type": "access",
  "jti": "51bff96e70c7474ab6b2c3c44c7d57a5",
  "exp": 1234567890
}
```

После login JTI сохраняется в Redis:

```text
wp:auth:user:4:access:51bff96e70c7474ab6b2c3c44c7d57a5
```

Значение ключа:

```text
valid
```

TTL ключа равен времени жизни access token.

Если `JWT_ACCESS_EXPIRE_MINUTES=15`, то TTL примерно равен:

```text
900 секунд
```

При каждом защищенном запросе приложение проверяет:

```text
1. Валидность JWT.
2. Тип токена: access.
3. Наличие sub.
4. Наличие jti.
5. Наличие соответствующего JTI-ключа в Redis.
6. Наличие активного токена в PostgreSQL.
```

Если JTI отсутствует в Redis, access token считается отозванным.

---

## Logout через Redis

При logout выполняется:

```text
1. Access token декодируется.
2. Из него извлекаются user_id и jti.
3. Redis-ключ JTI удаляется.
4. Кеш профиля пользователя удаляется.
5. Хеши access/refresh токенов помечаются как revoked в PostgreSQL.
6. Cookies access_token и refresh_token удаляются.
```

После logout старый access token больше не может использоваться, даже если срок его действия еще не истек.

Это решает проблему stateless JWT: токен остается криптографически валидным, но становится недействительным на уровне Redis-сессии.

---

## API endpoints

### System endpoints

| Метод | URI | Описание | Доступ |
| --- | --- | --- | --- |
| GET | `/` | Проверка работы API | Public |
| GET | `/db-check` | Проверка подключения к БД | Public |

---

### Auth endpoints

| Метод | URI | Описание | Доступ |
| --- | --- | --- | --- |
| POST | `/auth/register` | Регистрация пользователя | Public |
| POST | `/auth/login` | Логин, создание JTI в Redis и установка cookies | Public |
| GET | `/auth/whoami` | Получение текущего пользователя и кеширование профиля | Private |
| POST | `/auth/refresh` | Обновление access и refresh токенов | Public, нужен `refresh_token` cookie |
| POST | `/auth/logout` | Выход из текущей сессии, удаление JTI и профиля из Redis | Private |
| POST | `/auth/logout-all` | Выход со всех устройств | Private |
| GET | `/auth/oauth/yandex` | Начало OAuth-авторизации через Yandex ID | Public |
| GET | `/auth/oauth/yandex/callback` | Callback от Yandex ID | Public |
| POST | `/auth/forgot-password` | Генерация reset token | Public |
| POST | `/auth/reset-password` | Сброс пароля по reset token | Public |

---

### Items endpoints

Все `/items` endpoints требуют авторизацию через cookie `access_token`.

| Метод | URI | Описание |
| --- | --- | --- |
| POST | `/items` | Создать item и инвалидировать кеш списков |
| GET | `/items` | Получить список своих items с кешированием |
| GET | `/items/{item_id}` | Получить свой item по ID |
| PUT | `/items/{item_id}` | Полностью обновить item и инвалидировать кеш |
| PATCH | `/items/{item_id}` | Частично обновить item и инвалидировать кеш |
| DELETE | `/items/{item_id}` | Soft Delete item и инвалидировать кеш |

---

## Проверка через Swagger UI

Swagger UI доступен по адресу:

```text
http://localhost:8000/api/docs
```

---

### 1. Регистрация

Endpoint:

```text
POST /auth/register
```

Request body:

```json
{
  "email": "test@example.com",
  "password": "Password123"
}
```

Ожидаемый результат:

```text
201 Created
```

---

### 2. Логин

Endpoint:

```text
POST /auth/login
```

Request body:

```json
{
  "email": "test@example.com",
  "password": "Password123"
}
```

Ожидаемый результат:

```text
200 OK
```

После успешного входа backend устанавливает cookies:

```text
access_token
refresh_token
```

Также в Redis появляется JTI access-токена:

```text
wp:auth:user:{user_id}:access:{jti}
```

---

### 3. Проверка текущего пользователя

Endpoint:

```text
GET /auth/whoami
```

Ожидаемый результат:

```text
200 OK
```

После запроса в Redis появляется кеш профиля:

```text
wp:users:profile:{user_id}
```

---

### 4. Проверка кеширования items

Создать item:

```text
POST /items
```

Request body:

```json
{
  "name": "Ноутбук",
  "description": "Рабочий ноутбук для разработки"
}
```

Получить список:

```text
GET /items?limit=10&offset=0
```

После запроса в Redis появляется ключ:

```text
wp:items:list:user:{user_id}:limit:10:offset:0
```

---

### 5. Проверка инвалидации items

После того как кеш списка создан, выполнить:

```text
POST /items
```

или:

```text
PUT /items/{item_id}
PATCH /items/{item_id}
DELETE /items/{item_id}
```

После этого кеш списков пользователя должен быть удален.

---

### 6. Проверка logout

Endpoint:

```text
POST /auth/logout
```

После logout:

- cookies удаляются;
- JTI access-токена удаляется из Redis;
- кеш профиля пользователя удаляется из Redis;
- повторный запрос `GET /auth/whoami` возвращает `401 Unauthorized`.

---

## Проверка Redis через CLI

Подключиться к Redis CLI:

```bash
docker exec -it lab_redis redis-cli -a redis_secure_password_change_me
```

Проверить соединение:

```redis
PING
```

Ожидаемый ответ:

```text
PONG
```

---

### Просмотр всех ключей проекта

```redis
KEYS wp:*
```

---

### Проверка кеша items

```redis
KEYS wp:items:*
```

Пример результата:

```text
1) "wp:items:list:user:4:limit:10:offset:0"
```

Проверить TTL:

```redis
TTL wp:items:list:user:4:limit:10:offset:0
```

Пример результата:

```text
(integer) 176
```

Получить значение:

```redis
GET wp:items:list:user:4:limit:10:offset:0
```

---

### Проверка кеша профиля пользователя

```redis
KEYS wp:users:*
```

Пример результата:

```text
1) "wp:users:profile:4"
```

Проверить TTL:

```redis
TTL wp:users:profile:4
```

Получить значение:

```redis
GET wp:users:profile:4
```

Пример значения:

```json
"{\"id\": 4, \"email\": \"user@example.com\"}"
```

---

### Проверка JTI access-токена

```redis
KEYS wp:auth:*
```

Пример результата:

```text
1) "wp:auth:user:4:access:51bff96e70c7474ab6b2c3c44c7d57a5"
```

Проверить TTL:

```redis
TTL wp:auth:user:4:access:51bff96e70c7474ab6b2c3c44c7d57a5
```

Пример результата:

```text
(integer) 786
```

---

### Проверка logout

После выполнения:

```text
POST /auth/logout
```

проверить Redis:

```redis
KEYS wp:*
```

Ожидаемый результат:

```text
(empty array)
```

Если были созданы только auth/profile ключи текущего пользователя, после logout они должны исчезнуть.

---

### Очистка Redis для тестов

```redis
FLUSHDB
```

---

## Swagger / OpenAPI документация

В режиме разработки Swagger UI доступен по адресу:

```text
http://localhost:8000/api/docs
```

OpenAPI JSON доступен по адресу:

```text
http://localhost:8000/openapi.json
```

ReDoc доступен по адресу:

```text
http://localhost:8000/redoc
```

Документация содержит:

- группы endpoints;
- DTO-схемы;
- примеры запросов;
- примеры ответов;
- описания ошибок;
- cookie-based авторизацию;
- OAuth2 flow через Yandex ID.

---

## Production-режим

Документация доступна только в режиме разработки.

В `.env`:

```env
APP_ENV=development
```

Swagger доступен:

```text
http://localhost:8000/api/docs
```

Для проверки production-режима нужно изменить `.env`:

```env
APP_ENV=production
```

Перезапустить контейнеры:

```bash
docker compose down
docker compose up --build -d
```

После этого документация должна быть недоступна:

```text
http://localhost:8000/api/docs      → 404 Not Found
http://localhost:8000/redoc         → 404 Not Found
http://localhost:8000/openapi.json  → 404 Not Found
```

При этом основное API продолжает работать:

```text
http://localhost:8000/
```

После проверки production-режима нужно вернуть:

```env
APP_ENV=development
```

---

## Yandex OAuth

В проекте реализован OAuth-вход через **Yandex ID**.

Основной OAuth flow начинается через endpoint:

```text
GET /auth/oauth/yandex
```

Или напрямую в браузере:

```text
http://localhost:8000/auth/oauth/yandex
```

Далее:

1. Backend генерирует `oauth_state`.
2. `oauth_state` сохраняется в `HttpOnly` cookie.
3. Пользователь перенаправляется на страницу авторизации Яндекса.
4. После подтверждения Яндекс возвращает пользователя на backend callback.
5. Backend проверяет `state`.
6. Backend получает данные пользователя от Яндекса.
7. Backend создает или находит локального пользователя.
8. Backend создает JWT access и refresh tokens.
9. Access token получает уникальный `jti`.
10. JTI access-токена сохраняется в Redis.
11. Backend устанавливает `access_token` и `refresh_token` в `HttpOnly` cookies.
12. Пользователь перенаправляется на `CLIENT_URL`.

После этого можно проверить авторизацию:

```text
GET /auth/whoami
```

Ожидаемый результат:

```text
200 OK
```

---

## Безопасность

В проекте реализованы следующие меры безопасности:

| Механизм | Реализация |
| --- | --- |
| Хранение паролей | Только хеш + соль |
| Уникальная соль | Генерируется для каждого пользователя |
| Access Token | JWT, короткий срок жизни |
| Refresh Token | JWT, длительный срок жизни |
| Передача токенов | Через `HttpOnly` cookies |
| Хранение токенов в БД | В БД хранится только хеш токена |
| JTI access token | В Redis хранится только идентификатор токена |
| Полный access token в Redis | Не хранится |
| Пароли в Redis | Не хранятся |
| TTL ключей Redis | Используется для всех ключей |
| Redis password | Подключение защищено паролем |
| Logout | Удаляет JTI из Redis и помечает токены revoked в БД |
| Logout all | Удаляет все JTI пользователя и отзывает токены в БД |
| OAuth CSRF protection | Используется параметр `state` |
| Reset password | Reset token хранится в БД в виде хеша |
| Items ownership | Проверка `owner_id` |
| Swagger в production | Отключается через `APP_ENV=production` |

---

## Миграции базы данных

Миграции выполняются через Alembic.

Применить миграции:

```bash
docker exec -it lab_app python -m alembic upgrade head
```

Создать новую миграцию:

```bash
docker exec -it lab_app python -m alembic revision --autogenerate -m "migration name"
```

Основные таблицы:

| Таблица | Назначение |
| --- | --- |
| `users` | Пользователи |
| `auth_tokens` | Хеши access/refresh токенов |
| `items` | CRUD-ресурсы |
| `password_reset_tokens` | Хеши reset-токенов |

---

## Проверка данных в БД

### Проверка пользователей

```sql
SELECT id, email, password_hash, password_salt, yandex_id, created_at
FROM users
ORDER BY id ASC;
```

Пароли не должны храниться в открытом виде.

---

### Проверка токенов

```sql
SELECT id, user_id, token_type, token_hash, expires_at, revoked
FROM auth_tokens
ORDER BY id DESC;
```

В БД не должно быть исходных JWT, только их хеши.

---

### Проверка reset token

```sql
SELECT id, user_id, token_hash, expires_at, used
FROM password_reset_tokens
ORDER BY id DESC;
```

Reset token также хранится в виде хеша.

---

### Проверка Soft Delete

```sql
SELECT id, owner_id, name, description, deleted_at
FROM items
ORDER BY id ASC;
```

Удаленные записи остаются в базе, но имеют заполненное поле `deleted_at`.

---

## Контрольные вопросы

### 1. В чем разница между Cache-Aside и Write-Through?

**Cache-Aside** — приложение само управляет кешем.

Сначала оно проверяет кеш. Если данных нет, получает их из БД, кладет в кеш и возвращает клиенту.

```text
Read:
App → Redis
если miss:
App → PostgreSQL → Redis → Client
```

**Write-Through** — данные записываются в кеш и базу одновременно через единый слой записи.

При такой стратегии кеш обновляется сразу во время записи.

В данной лабораторной работе используется стратегия **Cache-Aside**.

---

### 2. Что такое Thundering Herd problem?

**Thundering Herd problem** — ситуация, когда много клиентов одновременно запрашивают один и тот же ключ после его истечения.

Например:

```text
Популярный ключ истек.
1000 запросов одновременно получили cache miss.
Все 1000 запросов пошли в PostgreSQL.
База получила резкий скачок нагрузки.
```

Кеш может как помочь, так и усугубить проблему.

Он помогает снижать нагрузку при cache hit, но при массовом cache miss может создать резкий всплеск запросов к базе.

---

### 3. Почему не рекомендуется использовать `KEYS *` в production?

Команда `KEYS *` сканирует все ключи Redis сразу.

На маленькой учебной базе это удобно, но в production это опасно:

- команда может выполняться долго;
- Redis однопоточный;
- другие запросы могут ждать завершения `KEYS`;
- возможна деградация производительности.

В коде лучше использовать `SCAN`, поэтому в проекте для удаления по паттерну используется:

```text
scan_iter(match=pattern)
```

---

### 4. Как обеспечить согласованность данных между БД и кешем при одновременной записи?

Основной способ — инвалидировать или обновлять кеш сразу после успешной записи в БД.

В этом проекте используется подход:

```text
1. Изменить данные в PostgreSQL.
2. Выполнить commit.
3. Удалить связанные ключи Redis.
4. Следующий GET заново заполнит кеш актуальными данными.
```

Такой подход уменьшает риск того, что пользователь получит устаревшие данные.

---

### 5. Зачем нужен TTL, если есть инвалидация кеша?

TTL нужен как дополнительная страховка.

Даже если инвалидация где-то не сработает, ключ не будет жить бесконечно.

Через заданное время Redis сам удалит устаревшие данные.

TTL также помогает:

- ограничивать использование памяти;
- автоматически очищать старые ключи;
- снижать риск вечного хранения неактуальных данных.

---

### 6. Почему хранение JTI в Redis позволяет реализовать мгновенный logout?

JWT обычно stateless.

Если токен подписан правильно и срок действия не истек, приложение считает его валидным.

JTI решает эту проблему.

Access token получает уникальный идентификатор:

```text
jti
```

Этот JTI сохраняется в Redis.

При каждом защищенном запросе приложение проверяет, существует ли JTI в Redis.

Если пользователь делает logout, ключ JTI удаляется:

```text
wp:auth:user:{user_id}:access:{jti}
```

После этого токен больше не принимается, даже если его `exp` еще не истек.

---

### 7. Какие данные безопасно кешировать, а какие нет?

Безопасно кешировать:

- ID пользователя;
- email;
- список items;
- публичные или несекретные поля ресурсов;
- JTI access-токена;
- технические значения вроде `valid`.

Нельзя кешировать:

- пароль;
- хеш пароля;
- соль пароля;
- полный access token;
- полный refresh token;
- reset token;
- чувствительные персональные данные без необходимости.

---

### 8. Как повлияет перезапуск Redis на работу приложения?

Redis используется как вспомогательный слой.

Если Redis перезапустится:

- часть кеша может быть потеряна;
- первые запросы снова пойдут в PostgreSQL;
- кеш постепенно заполнится заново.

В проекте включен AOF:

```text
--appendonly yes
```

Это позволяет Redis сохранять данные на диск.

Но приложение не должно полностью зависеть от кеша: основным источником данных остается PostgreSQL.

---

### 9. Что такое сериализация и зачем она нужна при сохранении объектов в Redis?

Redis хранит значения в виде строк.

Python-объекты, например SQLAlchemy-модели, нельзя напрямую сохранить в Redis.

Поэтому объект преобразуется в словарь, а затем в JSON-строку:

```text
Python object → dict → JSON string → Redis
```

При чтении происходит обратное преобразование:

```text
Redis string → JSON → Python dict
```

В проекте для этого используются:

```python
json.dumps()
json.loads()
```

---

### 10. Как префиксы ключей помогают в управлении кешем?

Префиксы помогают структурировать ключи и избегать конфликтов.

В проекте используется общий префикс:

```text
wp:
```

Примеры:

```text
wp:items:list:user:4:limit:10:offset:0
wp:users:profile:4
wp:auth:user:4:access:51bff96e70c7474ab6b2c3c44c7d57a5
```

Так можно удобно искать и удалять связанные ключи:

```redis
KEYS wp:items:*
KEYS wp:auth:*
KEYS wp:users:*
```

---

### 11. Зачем защищать Redis паролем даже внутри Docker-сети?

Redis может содержать важные данные:

- идентификаторы активных сессий;
- кеш пользовательских данных;
- технические ключи приложения.

Даже если Redis находится внутри Docker-сети, защита паролем снижает риск несанкционированного доступа при неправильной настройке сети, пробросе портов или компрометации соседнего контейнера.

В проекте Redis запускается с параметром:

```text
--requirepass ${REDIS_PASSWORD}
```

---

## Автор

Путинцев С.Р.  
090304-РПИб-о23