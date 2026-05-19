# Лабораторная работа №4  
## Автоматизированное документирование REST API с использованием OpenAPI / Swagger

Проект является продолжением **Лабораторной работы №3**.  
К существующему REST API на **FastAPI** добавлена полноценная автоматическая документация API на основе **OpenAPI** и **Swagger UI**.

В рамках работы были описаны endpoints, DTO-схемы, примеры запросов и ответов, возможные ошибки, cookie-based авторизация, OAuth через **Yandex ID**, а также реализовано отключение документации в production-режиме.

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Стек технологий](#стек-технологий)
- [Что реализовано в лабораторной №4](#что-реализовано-в-лабораторной-4)
- [Структура проекта](#структура-проекта)
- [Переменные окружения](#переменные-окружения)
- [Запуск через Docker](#запуск-через-docker)
- [Swagger / OpenAPI документация](#swagger--openapi-документация)
- [Схемы авторизации в Swagger UI](#схемы-авторизации-в-swagger-ui)
- [Production-режим](#production-режим)
- [API endpoints](#api-endpoints)
- [Проверка через Swagger UI](#проверка-через-swagger-ui)
- [Yandex OAuth](#yandex-oauth)
- [Безопасность документации](#безопасность-документации)
- [Реализованные меры безопасности](#реализованные-меры-безопасности)
- [Миграции базы данных](#миграции-базы-данных)
- [Проверка данных в БД](#проверка-данных-в-бд)
- [Контрольные вопросы](#контрольные-вопросы)
- [Финальная проверка перед сдачей](#финальная-проверка-перед-сдачей)
- [Автор](#автор)

---

## Описание проекта

REST API реализовано на **FastAPI** с использованием **PostgreSQL**, **SQLAlchemy**, **Alembic** и **Docker Compose**.

Проект наследует функциональность лабораторных работ №2 и №3:

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
- защита пользовательских ресурсов через `owner_id`.

В лабораторной работе №4 к проекту добавлена автоматическая документация API.  
Документация генерируется из кода приложения, Pydantic DTO и metadata в роутерах, то есть используется подход **Code-First**.

---

## Стек технологий

| Технология | Назначение |
| --- | --- |
| Python 3.11 | Язык программирования |
| FastAPI | Web API framework |
| OpenAPI | Спецификация описания REST API |
| Swagger UI | Интерактивный интерфейс документации |
| Pydantic | DTO, схемы данных и валидация |
| PostgreSQL 16 | База данных |
| SQLAlchemy | ORM |
| Alembic | Миграции базы данных |
| Uvicorn | ASGI-сервер |
| Docker / Docker Compose | Контейнеризация |
| python-jose | Работа с JWT |
| passlib / bcrypt | Хеширование паролей |
| httpx | HTTP-запросы к OAuth-провайдеру |
| Yandex ID | OAuth 2.0 провайдер |

---

## Что реализовано в лабораторной №4

| Требование | Реализация |
| --- | --- |
| Автоматическая OpenAPI-документация | ✅ Используется встроенная генерация FastAPI |
| Swagger UI | ✅ Доступен по `/api/docs` |
| Code-First подход | ✅ Документация собирается из кода, DTO и роутеров |
| Ручные YAML/JSON спецификации | ✅ Не используются |
| Группировка endpoints по тегам | ✅ `Auth`, `Items`, `System`, `Schemas` |
| Описания операций | ✅ Добавлены `summary` и `description` |
| Примеры request body | ✅ Добавлены через Pydantic `Field` |
| Примеры response body | ✅ Добавлены через `responses` |
| Примеры ошибок | ✅ Описаны `400`, `401`, `403`, `404`, `409` |
| DTO-схемы | ✅ Описаны через Pydantic-модели |
| Скрытие чувствительных данных | ✅ Пароли, соли и токены не отображаются в response schemas |
| Cookie-based auth | ✅ Добавлена OpenAPI security scheme `APIKeyCookie` для cookie `access_token` |
| Защищённые endpoints | ✅ Помечены значком замка в Swagger UI |
| Swagger Authorize | ✅ Доступны схемы `APIKeyCookie` и `YandexOAuth2` |
| OAuth Yandex | ✅ Описаны OAuth start, callback endpoints и OAuth2-схема `YandexOAuth2` |
| Production-режим | ✅ `/api/docs`, `/redoc`, `/openapi.json` отключаются |
| Docker Compose | ✅ Проект запускается через `docker-compose up --build` |

---

## Структура проекта

```text
app/
├── auth/
│   ├── dependencies.py      # получение текущего пользователя из access_token cookie
│   ├── oauth_yandex.py      # Yandex OAuth flow
│   ├── router.py            # auth endpoints + OpenAPI metadata
│   ├── security.py          # JWT, password hash, token hash
│   └── service.py           # auth business logic
│
├── models/
│   ├── auth_token.py
│   ├── item.py
│   ├── password_reset_token.py
│   └── user.py
│
├── routers/
│   └── item_router.py       # items CRUD endpoints + OpenAPI metadata
│
├── schemas/
│   ├── auth.py              # auth DTO + examples
│   ├── item.py              # item DTO + examples
│   └── user.py              # safe user response schema
│
├── services/
│   └── item_service.py
│
├── config.py
├── database.py
└── main.py                  # FastAPI app + Swagger/OpenAPI configuration
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

JWT_ACCESS_SECRET=change_me_access_secret
JWT_REFRESH_SECRET=change_me_refresh_secret
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:8000/auth/oauth/yandex/callback
CLIENT_URL=http://localhost:8000/api/docs
```

> Файл `.env` не должен попадать в GitHub, так как может содержать реальные секреты.

---

## Запуск через Docker

### 1. Клонировать репозиторий

```bash
git clone https://github.com/quazerbee/lab_2.git
cd lab_2
git checkout lab4-openapi
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Для Windows PowerShell:

```powershell
copy .env.example .env
```

Для запуска через Docker должно быть:

```env
DB_HOST=postgres
APP_ENV=development
```

### 3. Запустить контейнеры

```bash
docker-compose up --build -d
```

или:

```bash
docker compose up --build -d
```

### 4. Проверить контейнеры

```bash
docker ps
```

Должны быть запущены контейнеры:

```text
lab_app
lab_postgres
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

В документации реализованы разделы:

| Раздел | Назначение |
| --- | --- |
| `Auth` | Регистрация, логин, cookies, refresh, logout, OAuth, password reset |
| `Items` | CRUD-операции над пользовательскими ресурсами |
| `System` | Системные endpoints `/` и `/db-check` |
| `Schemas` | DTO-схемы запросов и ответов |

Документация содержит:

- названия операций;
- описания операций;
- теги;
- схемы DTO;
- примеры request body;
- примеры successful response;
- примеры ошибок;
- security schemes;
- OAuth2 flow.

---

## Схемы авторизации в Swagger UI

В Swagger UI доступна кнопка:

```text
Authorize
```

В документации описаны две схемы безопасности:

| Схема | Тип | Назначение |
| --- | --- | --- |
| `APIKeyCookie` | `apiKey` in cookie | Авторизация через cookie `access_token` |
| `YandexOAuth2` | OAuth2 Authorization Code Flow | Документирование OAuth2 flow через Yandex ID |

Защищённые endpoints помечены значком замка.

Примеры защищённых endpoints:

```text
GET /auth/whoami
POST /auth/logout-all
GET /items
POST /items
PUT /items/{item_id}
PATCH /items/{item_id}
DELETE /items/{item_id}
```

Основной сценарий проверки cookie-авторизации:

1. Выполнить `POST /auth/login`.
2. Backend установит `HttpOnly` cookies:
   - `access_token`;
   - `refresh_token`.
3. Выполнить `GET /auth/whoami`.
4. Если ответ `200 OK`, авторизация работает.
5. Выполнить `GET /items`.
6. Если ответ `200 OK`, защищённые CRUD endpoints доступны авторизованному пользователю.

> Токены не возвращаются в JSON response body.  
> Они передаются через `Set-Cookie` и сохраняются браузером как `HttpOnly` cookies.

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
docker-compose down
docker-compose up --build -d
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

Ожидаемый ответ:

```json
{
  "message": "API is working"
}
```

После проверки production-режима нужно вернуть:

```env
APP_ENV=development
```

и снова перезапустить контейнеры:

```bash
docker-compose up --build -d
```

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
| POST | `/auth/login` | Логин и установка `HttpOnly` cookies | Public |
| GET | `/auth/whoami` | Получение текущего пользователя | Private |
| POST | `/auth/refresh` | Обновление access и refresh токенов | Public, нужен `refresh_token` cookie |
| POST | `/auth/logout` | Выход из текущей сессии | Private |
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
| POST | `/items` | Создать item |
| GET | `/items` | Получить список своих items с пагинацией |
| GET | `/items/{item_id}` | Получить свой item по ID |
| PUT | `/items/{item_id}` | Полностью обновить item |
| PATCH | `/items/{item_id}` | Частично обновить item |
| DELETE | `/items/{item_id}` | Soft Delete item |

---

## Проверка через Swagger UI

Swagger UI:

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

Повторная регистрация с тем же email:

```text
409 Conflict
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

Cookies имеют флаг:

```text
HttpOnly
```

---

### 3. Проверка текущего пользователя

Endpoint:

```text
GET /auth/whoami
```

Если пользователь авторизован:

```text
200 OK
```

Если cookies отсутствуют или токен недействителен:

```text
401 Unauthorized
```

---

### 4. Обновление токенов

Endpoint:

```text
POST /auth/refresh
```

Использует `refresh_token` из cookies и выдаёт новую пару токенов:

```text
access_token
refresh_token
```

---

### 5. Выход из текущей сессии

Endpoint:

```text
POST /auth/logout
```

После logout cookies удаляются.

Проверка:

```text
GET /auth/whoami → 401 Unauthorized
```

---

### 6. Выход со всех устройств

Endpoint:

```text
POST /auth/logout-all
```

Отзывает все активные токены пользователя.

---

### 7. Password reset

Запрос reset token:

```text
POST /auth/forgot-password
```

Request body:

```json
{
  "email": "test@example.com"
}
```

Response body:

```json
{
  "message": "Password reset token generated successfully",
  "reset_token": "reset-token-example"
}
```

Смена пароля:

```text
POST /auth/reset-password
```

Request body:

```json
{
  "token": "reset-token-example",
  "new_password": "NewPassword123"
}
```

После успешной смены пароля:

```text
старый пароль → 401 Unauthorized
новый пароль → 200 OK
повторное использование reset token → ошибка
```

> В учебной реализации reset token возвращается в ответе.  
> В production-приложении такой токен должен отправляться пользователю по email.

---

### 8. Проверка защищённых items

Без логина:

```text
GET /items → 401 Unauthorized
```

После логина:

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

Ожидаемый ответ:

```json
{
  "id": 1,
  "name": "Ноутбук",
  "description": "Рабочий ноутбук для разработки",
  "owner_id": 1
}
```

Получение списка:

```text
GET /items?limit=10&offset=0
```

Удаление:

```text
DELETE /items/{item_id} → 204 No Content
```

После удаления item не должен возвращаться в обычных запросах:

```text
GET /items/{item_id} → 404 Not Found
```

---

## Yandex OAuth

В проекте реализован OAuth-вход через **Yandex ID**.

Есть два сценария использования OAuth.

---

### 1. Основной backend OAuth flow

Основной рабочий сценарий приложения начинается через endpoint:

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
7. Backend создаёт или находит локального пользователя.
8. Backend создаёт JWT access и refresh tokens.
9. Backend устанавливает `access_token` и `refresh_token` в `HttpOnly` cookies.
10. Пользователь перенаправляется на `CLIENT_URL`.

После этого можно проверить авторизацию:

```text
GET /auth/whoami
```

Ожидаемый результат:

```text
200 OK
```

---

### 2. Swagger OAuth2 flow

В Swagger UI также добавлена схема:

```text
YandexOAuth2
```

Она отображается в окне:

```text
Authorize
```

и документирует OAuth2 Authorization Code Flow через Yandex ID.

Swagger OAuth2 flow использует служебный redirect:

```text
http://localhost:8000/api/docs/oauth2-redirect
```

---

### Настройки приложения в Yandex OAuth

Для корректной работы нужно создать приложение в Yandex OAuth / Yandex ID.

Тип приложения:

```text
Для авторизации пользователей
```

Платформа:

```text
Веб-сервисы
```

В настройках приложения должны быть указаны два Callback URL:

```text
http://localhost:8000/auth/oauth/yandex/callback
http://localhost:8000/api/docs/oauth2-redirect
```

Назначение callback URL:

| Callback URL | Назначение |
| --- | --- |
| `/auth/oauth/yandex/callback` | Backend callback для реального входа через Яндекс |
| `/api/docs/oauth2-redirect` | Swagger UI redirect для схемы `YandexOAuth2` |

Рекомендуемые права:

```text
Доступ к адресу электронной почты
Доступ к логину, имени и фамилии, полу
```

После создания приложения нужно указать в `.env`:

```env
YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:8000/auth/oauth/yandex/callback
CLIENT_URL=http://localhost:8000/api/docs
```

---

## Безопасность документации

В лабораторной работе №4 отдельно проверяется, что документация не раскрывает чувствительные данные.

В Swagger-схемах ответов используется безопасная модель пользователя:

```text
UserResponse
```

Она содержит только:

```text
id
email
created_at
updated_at
deleted_at
```

В Swagger не отображаются:

```text
password
password_hash
password_salt
access_token
refresh_token
token_hash
```

Также документация отключается в production-режиме:

```env
APP_ENV=production
```

В этом режиме недоступны:

```text
/api/docs
/redoc
/openapi.json
```

---

## Реализованные меры безопасности

| Механизм | Реализация |
| --- | --- |
| Хранение паролей | Только хеш + соль |
| Уникальная соль | Генерируется для каждого пользователя |
| Access Token | JWT, короткий срок жизни |
| Refresh Token | JWT, длительный срок жизни |
| Передача токенов | Через `HttpOnly` cookies |
| Хранение токенов | В БД хранится только хеш токена |
| Logout | Токены помечаются как `revoked=True` |
| Logout all | Отзываются все токены пользователя |
| OAuth CSRF protection | Используется параметр `state` |
| Reset password | Reset token хранится в БД в виде хеша |
| Items ownership | Проверка `owner_id` |
| Swagger Cookie Auth | `APIKeyCookie` для cookie `access_token` |
| Swagger OAuth2 | `YandexOAuth2` Authorization Code Flow |
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

Удалённые записи остаются в базе, но имеют заполненное поле `deleted_at`.

---

## Контрольные вопросы

### 1. Что такое спецификация OpenAPI и чем она отличается от Swagger UI?

**OpenAPI** — это спецификация, которая описывает REST API в стандартизированном виде: пути, HTTP-методы, параметры, request body, response body, схемы данных, коды ответов и способы авторизации.

**Swagger UI** — это визуальный интерфейс, который отображает OpenAPI-спецификацию в браузере и позволяет тестировать API.

Иными словами:

```text
OpenAPI — это описание API.
Swagger UI — это интерфейс для просмотра и тестирования этого описания.
```

---

### 2. Какие существуют подходы к созданию документации: Code-First и Design-First? Какой использовался в этой работе?

Существует два основных подхода:

| Подход | Описание |
| --- | --- |
| Code-First | Сначала пишется код приложения, затем документация генерируется из кода |
| Design-First | Сначала вручную проектируется OpenAPI-спецификация, затем по ней реализуется API |

В этой работе использовался **Code-First** подход.

FastAPI автоматически генерирует OpenAPI-документацию на основе:

- роутеров;
- Pydantic DTO;
- типов данных;
- параметров функций;
- `summary`;
- `description`;
- `responses`;
- security schemes.

Плюсы Code-First:

- документация ближе к реальному коду;
- меньше риска рассинхронизации;
- быстрее в небольших проектах;
- удобно для учебного REST API.

Минусы:

- сложнее заранее проектировать API-контракт;
- документация зависит от качества аннотаций в коде;
- без дополнительных описаний Swagger может быть слишком сухим.

---

### 3. Почему важно скрывать документацию API в production?

Открытая документация в production может раскрывать лишнюю информацию:

- список всех endpoints;
- структуру DTO;
- protected routes;
- параметры запросов;
- возможные ошибки;
- внутренние названия сущностей;
- схемы авторизации.

Это может помочь злоумышленнику быстрее понять устройство API и подобрать вектор атаки.

В проекте документация отключается при:

```env
APP_ENV=production
```

В этом режиме недоступны:

```text
/api/docs
/redoc
/openapi.json
```

---

### 4. Как правильно документировать схемы безопасности, если приложение использует HttpOnly Cookies?

Если приложение использует `HttpOnly` cookies, токен нельзя вручную прочитать через JavaScript. Браузер сам отправляет cookies при запросах к тому же домену.

В OpenAPI такую авторизацию можно описать через схему типа `apiKey` с расположением `in: cookie`.

В этом проекте используется схема:

```text
APIKeyCookie
```

Cookie:

```text
access_token
```

Сценарий проверки:

1. Выполнить `POST /auth/login`.
2. Сервер установит `HttpOnly` cookies.
3. Выполнить защищённый endpoint, например `GET /auth/whoami`.
4. Браузер автоматически отправит cookies.
5. Если токен валиден, API вернёт `200 OK`.

---

### 5. Зачем нужны примеры в документации API?

Примеры помогают быстрее понять, как использовать API.

Они показывают:

- какие поля нужно отправлять;
- какие значения являются валидными;
- как выглядит успешный ответ;
- как выглядят ошибки;
- как устроены вложенные объекты;
- как frontend-разработчику обрабатывать ответы.

Например, вместо абстрактного body:

```json
{
  "email": "string",
  "password": "string"
}
```

Swagger показывает понятный пример:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

---

### 6. Какие HTTP-коды ответов обязательно должны быть описаны для CRUD операций?

Для CRUD-операций обычно описываются:

| Код | Значение | Когда используется |
| --- | --- | --- |
| 200 | OK | Успешное получение или обновление |
| 201 | Created | Успешное создание ресурса |
| 204 | No Content | Успешное удаление без тела ответа |
| 400 | Bad Request | Некорректные параметры запроса |
| 401 | Unauthorized | Пользователь не авторизован |
| 403 | Forbidden | Нет прав на ресурс |
| 404 | Not Found | Ресурс не найден |
| 409 | Conflict | Конфликт данных, например дубликат |
| 422 | Unprocessable Entity | Ошибка валидации Pydantic |
| 500 | Internal Server Error | Внутренняя ошибка сервера |

---

## Финальная проверка перед сдачей

Перед сдачей проекта проверьте:

- [ ] Создана отдельная ветка `lab4-openapi`.
- [ ] `docker-compose up --build -d` запускает проект.
- [ ] `docker exec -it lab_app python -m alembic upgrade head` применяет миграции.
- [ ] При `APP_ENV=development` Swagger доступен по `/api/docs`.
- [ ] При `APP_ENV=production` `/api/docs` возвращает `404 Not Found`.
- [ ] При `APP_ENV=production` основное API `/` продолжает работать.
- [ ] В Swagger есть группы `Auth`, `Items`, `System`, `Schemas`.
- [ ] В Swagger UI есть кнопка `Authorize`.
- [ ] В `Authorize` есть схема `APIKeyCookie`.
- [ ] В `Authorize` есть схема `YandexOAuth2`.
- [ ] Защищённые endpoints помечены значком замка.
- [ ] Все endpoints из лабораторных №2 и №3 отображаются.
- [ ] У endpoints есть `summary` и `description`.
- [ ] У успешных ответов есть примеры.
- [ ] У ошибок `400`, `401`, `403`, `404`, `409` есть примеры.
- [ ] DTO содержат descriptions и examples.
- [ ] `UserResponse` не содержит пароли, соли, токены и `token_hash`.
- [ ] `/auth/login` устанавливает `HttpOnly` cookies.
- [ ] `/auth/whoami` работает после логина.
- [ ] `/items` защищены авторизацией.
- [ ] Yandex OAuth работает через `/auth/oauth/yandex`.
- [ ] Swagger OAuth2 redirect добавлен в callback URLs Яндекс-приложения.
- [ ] `.env.example` содержит все нужные переменные.
- [ ] `.env` не попал в GitHub.
- [ ] Проект запушен на GitHub/GitLab.

---

## Автор

Путинцев С.Р.  
090304-РПИб-о23