# FastAPI Auth Project — Lab 3

## Описание

Проект представляет собой REST API на FastAPI с использованием PostgreSQL, SQLAlchemy, Alembic и Docker.

Лабораторная работа №3 является продолжением Лабораторной работы №2.  
К CRUD-функционалу добавлена система аутентификации и авторизации:

- регистрация пользователей;
- вход по email и паролю;
- хранение паролей в виде хеша с уникальной солью;
- выдача Access и Refresh JWT;
- передача токенов через `HttpOnly` cookies;
- хранение хешей токенов в базе данных;
- обновление токенов через refresh token;
- выход из текущей сессии;
- выход из всех сессий;
- проверка текущего пользователя через `/auth/whoami`;
- восстановление пароля через reset token;
- OAuth-вход через Yandex ID;
- защита CRUD-ресурсов авторизацией;
- проверка владения ресурсом через `owner_id`.

---

## Технологии

- Python 3.11
- FastAPI
- PostgreSQL 16
- SQLAlchemy
- Alembic
- Pydantic
- Uvicorn
- Docker / Docker Compose
- JWT (`python-jose`)
- bcrypt / passlib
- httpx
- Yandex ID OAuth

---

## Архитектура проекта

Проект построен по модульной структуре:

```text
app/
├── auth/          # логика аутентификации, JWT, OAuth, зависимости
├── models/        # SQLAlchemy ORM-модели
├── routers/       # API-роутеры
├── schemas/       # DTO / Pydantic-схемы
├── services/      # бизнес-логика
├── config.py      # настройки приложения
├── database.py    # подключение к БД
└── main.py        # точка входа FastAPI

| Метод | Endpoint                      | Описание                          | Доступ                       |
| ----- | ----------------------------- | --------------------------------- | ---------------------------- |
| POST  | `/auth/register`              | Регистрация пользователя          | Public                       |
| POST  | `/auth/login`                 | Вход и установка cookies          | Public                       |
| POST  | `/auth/refresh`               | Обновление access/refresh токенов | Public, нужен refresh cookie |
| GET   | `/auth/whoami`                | Получение текущего пользователя   | Private                      |
| POST  | `/auth/logout`                | Выход из текущей сессии           | Private                      |
| POST  | `/auth/logout-all`            | Выход из всех сессий              | Private                      |
| GET   | `/auth/oauth/yandex`          | Старт OAuth через Yandex ID       | Public                       |
| GET   | `/auth/oauth/yandex/callback` | Callback от Yandex ID             | Public                       |
| POST  | `/auth/forgot-password`       | Генерация reset token             | Public                       |
| POST  | `/auth/reset-password`        | Смена пароля по reset token       | Public                       |


| Метод  | Endpoint      | Описание                         | Доступ  |
| ------ | ------------- | -------------------------------- | ------- |
| POST   | `/items`      | Создать item                     | Private |
| GET    | `/items`      | Получить список своих items      | Private |
| GET    | `/items/{id}` | Получить свой item по ID         | Private |
| PUT    | `/items/{id}` | Полное обновление своего item    | Private |
| PATCH  | `/items/{id}` | Частичное обновление своего item | Private |
| DELETE | `/items/{id}` | Soft Delete своего item          | Private |

Переменные окружения

Создайте файл .env на основе .env.example:

cp .env.example .env

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

Файл .env не хранится в репозитории и не должен попадать на GitHub.

Запуск через Docker
1. Создать .env
cp .env.example .env
Заполните переменные окружения.
Для локального запуска через Docker значение должно быть: DB_HOST=postgres

2. Запустить контейнеры
docker compose up -d --build

3. Применить миграции
docker exec -it lab_app python -m alembic upgrade head

4. Открыть Swagger
http://localhost:8000/docs

Локальный запуск без Docker
1. Клонировать проект
git clone <your-repo-url>
cd lab_2

2. Создать виртуальное окружение
python -m venv venv

Для Windows PowerShell: .\venv\Scripts\Activate.ps1

3. Установить зависимости
pip install -r requirements.txt

4. Настроить .env

Для локального запуска без Docker: DB_HOST=localhost

5. Применить миграции
python -m alembic upgrade head

6. Запустить сервер
uvicorn app.main:app --reload

Swagger: http://localhost:8000/docs

Yandex OAuth

Для проверки OAuth-входа необходимо создать приложение в Yandex OAuth.

Тип приложения:

Для авторизации пользователей

Платформа: Веб-сервисы

Redirect URI: http://localhost:8000/auth/oauth/yandex/callback

Необходимые права:

Доступ к адресу электронной почты
Доступ к логину, имени и фамилии, полу

После создания приложения нужно указать в .env:

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:8000/auth/oauth/yandex/callback
CLIENT_URL=http://localhost:8000/docs

Проверка OAuth:

Запустить приложение.
Открыть в браузере: http://localhost:8000/auth/oauth/yandex
Подтвердить вход через Яндекс.
После редиректа обратно в Swagger вызвать: GET /auth/whoami

Если OAuth прошёл успешно, вернётся профиль пользователя.

Примеры запросов
Регистрация
POST /auth/register

{
  "email": "test@example.com",
  "password": "Password123"
}

Успешный ответ:

{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "created_at": "...",
    "updated_at": "...",
    "deleted_at": null
  }
}

Логин
POST /auth/login

{
  "email": "test@example.com",
  "password": "Password123"
}

После успешного входа сервер устанавливает cookies:

access_token
refresh_token

Обе cookies имеют флаг: HttpOnly

Проверка текущего пользователя
GET /auth/whoami

Если пользователь авторизован:

{
  "message": "User is authenticated",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "created_at": "...",
    "updated_at": "...",
    "deleted_at": null
  }
}

Если пользователь не авторизован:

{
  "detail": "Not authenticated"
}

Обновление токенов
POST /auth/refresh Использует refresh_token из cookies.

Logout
POST /auth/logout Завершает текущую сессию и удаляет cookies.

Logout All
POST /auth/logout-all Отзывает все активные токены пользователя.

Forgot Password
POST /auth/forgot-password

{
  "email": "test@example.com"
}

Ответ:

{
  "message": "Password reset token generated successfully",
  "reset_token": "..."
}

В учебной реализации reset token возвращается в ответе для удобства тестирования.
В production-приложении такой токен должен отправляться пользователю по email.

Reset Password
POST /auth/reset-password

{
  "token": "reset_token_here",
  "new_password": "NewPassword123"
}

После смены пароля старые auth-токены пользователя отзываются.

Создание item
Требуется авторизация.

POST /items

{
  "name": "My private item",
  "description": "Created by authenticated user"
}

Ответ:

{
  "id": 1,
  "owner_id": 1,
  "name": "My private item",
  "description": "Created by authenticated user"
}

Получение items
GET /items?limit=10&offset=0

Ответ:

{
  "data": [
    {
      "id": 1,
      "owner_id": 1,
      "name": "My private item",
      "description": "Created by authenticated user"
    }
  ],
  "meta": {
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}

Безопасность

В проекте реализованы следующие механизмы безопасности:

пароли не хранятся в открытом виде;
для каждого пароля используется уникальная соль;
пароли хешируются;
Access и Refresh токены передаются через HttpOnly cookies;
токены в базе данных хранятся только в виде хешей;
Refresh Token хранится на сервере и может быть отозван;
реализован logout текущей сессии;
реализован logout всех сессий;
OAuth state используется для защиты от CSRF;
чувствительные данные не возвращаются в API-ответах;
.env исключён из Git;
CRUD-ресурсы защищены авторизацией;
реализована проверка владения ресурсом через owner_id.

Модели базы данных

Основные таблицы:

users
auth_tokens
items
password_reset_tokens
users

Содержит данные пользователей:

id
email
password_hash
password_salt
yandex_id
vk_id
created_at
updated_at
deleted_at
auth_tokens

Содержит хеши access/refresh токенов:

id
user_id
token_hash
token_type
expires_at
revoked
created_at
items

Содержит CRUD-ресурсы:

id
owner_id
name
description
created_at
updated_at
deleted_at
password_reset_tokens

Содержит хеши reset-токенов:

id
user_id
token_hash
expires_at
used
created_at
Миграции

Миграции выполняются через Alembic.

Применить миграции внутри Docker:

docker exec -it lab_app python -m alembic upgrade head

Создать новую миграцию:

docker exec -it lab_app python -m alembic revision --autogenerate -m "migration name"
Проверка работы

Основные сценарии для проверки:

Регистрация пользователя.
Повторная регистрация с тем же email должна вернуть 409 Conflict.
Логин с правильным паролем должен вернуть 200 OK.
Логин с неправильным паролем должен вернуть 401 Unauthorized.
После логина /auth/whoami должен вернуть пользователя.
Без cookies /auth/whoami должен вернуть 401 Unauthorized.
/auth/refresh должен обновлять пару токенов.
/auth/logout должен завершать текущую сессию.
/auth/logout-all должен завершать все сессии.
/items без авторизации должен вернуть 401 Unauthorized.
/items после логина должен работать.
Пользователь должен видеть только свои items.
Soft Delete должен скрывать удалённые items.
Yandex OAuth должен создавать/находить пользователя и авторизовывать его.
Forgot/reset password должен менять пароль.
Повторное использование reset token должно вернуть 401 Unauthorized.

Проверка одинаковых паролей

Для проверки уникальной соли можно зарегистрировать двух пользователей с одинаковым паролем:

{
  "email": "user1@example.com",
  "password": "Password123"
}
{
  "email": "user2@example.com",
  "password": "Password123"
}

После этого в базе данных значения password_hash должны отличаться.

Пример SQL-запроса:

SELECT id, email, password_hash, password_salt
FROM users
ORDER BY id ASC;
Проверка токенов в БД

Токены в базе данных хранятся в виде хешей:

SELECT id, user_id, token_type, token_hash, expires_at, revoked
FROM auth_tokens
ORDER BY id DESC;

Исходные значения JWT в базе данных не хранятся.

Обработка ошибок
400 Bad Request — неверные параметры запроса.
401 Unauthorized — пользователь не авторизован, токен отсутствует или невалиден.
403 Forbidden — недостаточно прав для доступа к ресурсу.
404 Not Found — ресурс не найден.
409 Conflict — конфликт данных, например повторный email.
500 Internal Server Error — внутренняя ошибка сервера.
Автор

Путинцев С.Р
090304-РПИб-о23