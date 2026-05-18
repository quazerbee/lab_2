# Лабораторная работа №3  
## Авторизация и аутентификация: JWT, OAuth2, Cookies

Проект является продолжением **Лабораторной работы №2**.  
К CRUD API на FastAPI добавлена система аутентификации, авторизации, JWT-сессий, OAuth-входа через Yandex ID и защиты пользовательских ресурсов.

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Стек технологий](#стек-технологий)
- [Что реализовано](#что-реализовано)
- [Структура проекта](#структура-проекта)
- [Переменные окружения](#переменные-окружения)
- [Запуск через Docker](#запуск-через-docker)
- [Миграции базы данных](#миграции-базы-данных)
- [API эндпоинты](#api-эндпоинты)
- [Проверка через Swagger](#проверка-через-swagger)
- [Yandex OAuth](#yandex-oauth)
- [Безопасность](#безопасность)
- [Проверка данных в БД](#проверка-данных-в-бд)
- [Автор](#автор)

---

## Описание проекта

REST API реализовано на **FastAPI** с использованием **PostgreSQL**, **SQLAlchemy**, **Alembic** и **Docker**.

В рамках лабораторной работы реализованы:

- регистрация пользователей;
- вход по email и паролю;
- хеширование паролей с уникальной солью;
- Access Token и Refresh Token;
- передача токенов через `HttpOnly` cookies;
- хранение хешей токенов в базе данных;
- обновление токенов через `/auth/refresh`;
- выход из текущей сессии;
- выход из всех сессий;
- эндпоинт `/auth/whoami`;
- OAuth-вход через **Yandex ID**;
- восстановление пароля через reset token;
- защита CRUD-ресурсов из лабораторной №2;
- проверка владения ресурсом через `owner_id`.

---

## Стек технологий

| Технология | Назначение |
| --- | --- |
| Python 3.11 | Язык программирования |
| FastAPI | Web API framework |
| PostgreSQL 16 | База данных |
| SQLAlchemy | ORM |
| Alembic | Миграции БД |
| Pydantic | DTO и валидация |
| Uvicorn | ASGI-сервер |
| Docker / Docker Compose | Контейнеризация |
| python-jose | Работа с JWT |
| passlib / bcrypt | Хеширование паролей |
| httpx | HTTP-запросы к OAuth-провайдеру |
| Yandex ID | OAuth 2.0 провайдер |

---

## Что реализовано

### Auth

| Функция | Статус |
| --- | --- |
| Регистрация пользователя | ✅ |
| Логин по email и паролю | ✅ |
| JWT Access Token | ✅ |
| JWT Refresh Token | ✅ |
| `HttpOnly` cookies | ✅ |
| Хранение хешей токенов в БД | ✅ |
| Refresh token flow | ✅ |
| Logout текущей сессии | ✅ |
| Logout всех сессий | ✅ |
| `/auth/whoami` | ✅ |
| OAuth через Yandex ID | ✅ |
| Forgot password | ✅ |
| Reset password | ✅ |

### CRUD из лабораторной №2

| Функция | Статус |
| --- | --- |
| Создание ресурса | ✅ |
| Получение списка с пагинацией | ✅ |
| Получение по ID | ✅ |
| PUT обновление | ✅ |
| PATCH обновление | ✅ |
| Soft Delete | ✅ |
| Защита авторизацией | ✅ |
| Проверка владельца ресурса | ✅ |

---

## Структура проекта

```text
app/
├── auth/
│   ├── dependencies.py      # получение текущего пользователя
│   ├── oauth_yandex.py      # ручная реализация Yandex OAuth
│   ├── router.py            # auth endpoints
│   ├── security.py          # JWT, hash password, hash token
│   └── service.py           # auth business logic
│
├── models/
│   ├── auth_token.py
│   ├── item.py
│   ├── password_reset_token.py
│   └── user.py
│
├── routers/
│   └── item_router.py
│
├── schemas/
│   ├── auth.py
│   ├── item.py
│   └── user.py
│
├── services/
│   └── item_service.py
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

Пример `.env.example`:

```env
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
CLIENT_URL=http://localhost:8000/docs
```

> Файл `.env` не должен попадать в GitHub.

---

## Запуск через Docker

### 1. Клонировать репозиторий

```bash
git clone https://github.com/quazerbee/lab_2.git
cd lab_2
git checkout lab3-auth
```

### 2. Создать `.env`

```bash
cp .env.example .env
```

Для запуска через Docker должно быть:

```env
DB_HOST=postgres
```

### 3. Запустить контейнеры

```bash
docker compose up -d --build
```

### 4. Применить миграции

```bash
docker exec -it lab_app python -m alembic upgrade head
```

### 5. Открыть Swagger

```text
http://localhost:8000/docs
```

---

## Локальный запуск без Docker

### 1. Создать виртуальное окружение

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить `.env`

Для локального запуска без Docker:

```env
DB_HOST=localhost
```

### 4. Применить миграции

```bash
python -m alembic upgrade head
```

### 5. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Swagger:

```text
http://localhost:8000/docs
```

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

## API эндпоинты

### Auth endpoints

| Метод | URI | Описание | Доступ |
| --- | --- | --- | --- |
| POST | `/auth/register` | Регистрация | Public |
| POST | `/auth/login` | Логин и установка cookies | Public |
| POST | `/auth/refresh` | Обновление токенов | Public, нужен refresh cookie |
| GET | `/auth/whoami` | Получение текущего пользователя | Private |
| POST | `/auth/logout` | Выход из текущей сессии | Private |
| POST | `/auth/logout-all` | Выход из всех сессий | Private |
| GET | `/auth/oauth/yandex` | Старт OAuth через Yandex ID | Public |
| GET | `/auth/oauth/yandex/callback` | Callback от Yandex ID | Public |
| POST | `/auth/forgot-password` | Генерация reset token | Public |
| POST | `/auth/reset-password` | Смена пароля | Public |

### Items endpoints

Все `/items` endpoints требуют авторизацию.

| Метод | URI | Описание |
| --- | --- | --- |
| POST | `/items` | Создать item |
| GET | `/items` | Получить список своих items |
| GET | `/items/{item_id}` | Получить свой item по ID |
| PUT | `/items/{item_id}` | Полное обновление |
| PATCH | `/items/{item_id}` | Частичное обновление |
| DELETE | `/items/{item_id}` | Soft Delete |

---

## Проверка через Swagger

Swagger доступен по адресу:

```text
http://localhost:8000/docs
```

### 1. Регистрация

```json
POST /auth/register

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

```json
POST /auth/login

{
  "email": "test@example.com",
  "password": "Password123"
}
```

Ожидаемый результат:

```text
200 OK
```

После успешного входа сервер устанавливает cookies:

```text
access_token
refresh_token
```

---

### 3. Whoami

```text
GET /auth/whoami
```

Если пользователь авторизован:

```text
200 OK
```

Если cookies отсутствуют:

```text
401 Unauthorized
```

---

### 4. Refresh

```text
POST /auth/refresh
```

Использует `refresh_token` из cookies и выдаёт новую пару токенов.

---

### 5. Logout

```text
POST /auth/logout
```

Завершает текущую сессию.

После logout:

```text
GET /auth/whoami → 401 Unauthorized
```

---

### 6. Logout All

```text
POST /auth/logout-all
```

Отзывает все активные токены пользователя.

---

### 7. Password reset

Запрос reset token:

```json
POST /auth/forgot-password

{
  "email": "test@example.com"
}
```

Ответ:

```json
{
  "message": "Password reset token generated successfully",
  "reset_token": "..."
}
```

Смена пароля:

```json
POST /auth/reset-password

{
  "token": "reset_token_here",
  "new_password": "NewPassword123"
}
```

После смены пароля:

```text
старый пароль → 401
новый пароль → 200
повторное использование reset token → 401
```

> В учебной реализации reset token возвращается в ответе.  
> В production-приложении он должен отправляться пользователю по email.

---

### 8. Проверка защищённых items

Без логина:

```text
GET /items → 401 Unauthorized
```

После логина:

```json
POST /items

{
  "name": "My private item",
  "description": "Created by authenticated user"
}
```

Ожидаемый ответ:

```json
{
  "id": 1,
  "owner_id": 1,
  "name": "My private item",
  "description": "Created by authenticated user"
}
```

Проверка списка:

```text
GET /items?limit=10&offset=0
```

После удаления:

```text
DELETE /items/{item_id} → 204 No Content
GET /items/{item_id} → 404 Not Found
```

---

## Yandex OAuth

Для проверки OAuth нужно создать приложение в Yandex OAuth.

### Настройки приложения

Тип приложения:

```text
Для авторизации пользователей
```

Платформа:

```text
Веб-сервисы
```

Redirect URI:

```text
http://localhost:8000/auth/oauth/yandex/callback
```

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
CLIENT_URL=http://localhost:8000/docs
```

### Проверка OAuth

Откройте в браузере:

```text
http://localhost:8000/auth/oauth/yandex
```

Далее:

1. Происходит редирект на Яндекс.
2. Пользователь подтверждает вход.
3. Яндекс возвращает пользователя на callback.
4. Backend создаёт или находит локального пользователя.
5. Backend устанавливает `HttpOnly` cookies.
6. Пользователь возвращается на Swagger.
7. Проверка:

```text
GET /auth/whoami
```

Ожидаемый результат:

```text
200 OK
```

---

## Безопасность

В проекте реализованы следующие меры:

| Механизм | Реализация |
| --- | --- |
| Хранение паролей | Только хеш + соль |
| Уникальная соль | Генерируется для каждого пользователя |
| Access Token | JWT, короткий срок жизни |
| Refresh Token | JWT, длительный срок жизни |
| Передача токенов | Только через `HttpOnly` cookies |
| Хранение токенов | В БД хранится только хеш токена |
| Logout | Токен помечается как `revoked=True` |
| Logout all | Отзываются все токены пользователя |
| OAuth CSRF protection | Используется параметр `state` |
| Reset password | Reset token хранится в БД в виде хеша |
| Items ownership | Проверка `owner_id` |

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

### Проверка одинаковых паролей

Зарегистрируйте двух пользователей с одинаковым паролем:

```json
{
  "email": "user1@example.com",
  "password": "Password123"
}
```

```json
{
  "email": "user2@example.com",
  "password": "Password123"
}
```

Проверка:

```sql
SELECT id, email, password_hash, password_salt
FROM users
ORDER BY id ASC;
```

`password_hash` и `password_salt` должны отличаться.

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

## Обработка ошибок

| Код | Значение |
| --- | --- |
| 400 | Неверные параметры запроса |
| 401 | Не авторизован |
| 403 | Недостаточно прав |
| 404 | Ресурс не найден |
| 409 | Конфликт данных |
| 422 | Ошибка валидации |
| 500 | Внутренняя ошибка сервера |

---

## Финальная проверка перед сдачей

Перед сдачей проекта проверьте:

- [ ] `docker compose up -d --build` запускает проект.
- [ ] `alembic upgrade head` применяет миграции.
- [ ] Swagger открывается.
- [ ] Регистрация работает.
- [ ] Логин работает.
- [ ] Cookies устанавливаются как `HttpOnly`.
- [ ] `/auth/whoami` работает после логина.
- [ ] `/auth/refresh` обновляет токены.
- [ ] `/auth/logout` завершает текущую сессию.
- [ ] `/auth/logout-all` завершает все сессии.
- [ ] Yandex OAuth работает.
- [ ] `/items` защищены авторизацией.
- [ ] Пользователь видит только свои items.
- [ ] Soft Delete работает.
- [ ] Forgot/reset password работает.
- [ ] `.env` не попал в Git.
- [ ] В `docker-compose.yml` нет настоящих секретов.

---

## Автор

Путинцев С.Р.  
090304-РПИб-о23