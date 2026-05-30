# Лабораторная работа №7 — MinIO Object Storage

## Описание проекта

Проект представляет собой REST API на FastAPI с авторизацией, MongoDB, Redis и объектным хранилищем MinIO.

В рамках лабораторной работы №7 реализовано хранение файлов через MinIO. Файлы не сохраняются в файловой системе приложения и не хранятся в MongoDB как BLOB. В базе данных сохраняются только метаданные файлов: оригинальное имя, размер, MIME-type, bucket, object key и владелец файла.

Также реализовано обновление профиля пользователя с возможностью установки аватара через `avatar_file_id`.

## Используемые технологии

* Python 3.11
* FastAPI
* Uvicorn
* MongoDB
* Beanie ODM
* Redis
* MinIO
* Docker
* Docker Compose
* JWT Auth
* Swagger/OpenAPI

## Запуск проекта

### 1. Клонировать репозиторий

```bash
git clone https://github.com/quazerbee/lab_2.git
cd lab_2
```

### 2. Переключиться на ветку лабораторной работы №7

```bash
git checkout lab7-minio-storage
```

### 3. Создать `.env` файл

Можно использовать `.env.example` как основу:

```bash
cp .env.example .env
```

Пример `.env`:

```env
APP_ENV=development

DB_USER=student
DB_PASSWORD=student
DB_NAME=lab_db
MONGO_URI=mongodb://student:student@mongo:27017/lab_db?authSource=admin

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_secure_password_change_me
CACHE_TTL_DEFAULT=300

JWT_ACCESS_SECRET=super_access_secret_key
JWT_REFRESH_SECRET=super_refresh_secret_key
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=7

YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
YANDEX_CALLBACK_URL=http://localhost:8000/auth/oauth/yandex/callback
CLIENT_URL=http://localhost:8000/api/docs

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_secure_password_change_in_prod
MINIO_BUCKET=wp-labs-files
MINIO_USE_SSL=false
MAX_FILE_SIZE=10485760
```

### 4. Запустить проект

```bash
docker compose up --build
```

Или в фоновом режиме:

```bash
docker compose up --build -d
```

## Адреса сервисов

### Swagger UI

```text
http://localhost:8000/api/docs
```

### MinIO Console

```text
http://localhost:9001
```

Данные для входа в MinIO берутся из `.env`:

```text
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_secure_password_change_in_prod
```

## Основные эндпоинты API

### Auth

| Метод | URI                           | Описание                              |
| ----- | ----------------------------- | ------------------------------------- |
| POST  | `/auth/register`              | Регистрация пользователя              |
| POST  | `/auth/login`                 | Авторизация пользователя              |
| GET   | `/auth/whoami`                | Получение текущего пользователя       |
| POST  | `/auth/refresh`               | Обновление JWT-токенов                |
| POST  | `/auth/logout`                | Выход из текущей сессии               |
| POST  | `/auth/logout-all`            | Выход со всех устройств               |
| GET   | `/auth/oauth/yandex`          | Начало OAuth-авторизации через Яндекс |
| GET   | `/auth/oauth/yandex/callback` | Callback от Яндекс OAuth              |
| POST  | `/auth/forgot-password`       | Запрос сброса пароля                  |
| POST  | `/auth/reset-password`        | Сброс пароля                          |

### Items

| Метод  | URI                | Описание                                    |
| ------ | ------------------ | ------------------------------------------- |
| POST   | `/items`           | Создать item                                |
| GET    | `/items`           | Получить список items текущего пользователя |
| GET    | `/items/{item_id}` | Получить item по ID                         |
| PUT    | `/items/{item_id}` | Полностью обновить item                     |
| PATCH  | `/items/{item_id}` | Частично обновить item                      |
| DELETE | `/items/{item_id}` | Удалить item                                |

### Files

| Метод  | URI                | Описание               |
| ------ | ------------------ | ---------------------- |
| POST   | `/files`           | Загрузить файл в MinIO |
| GET    | `/files/{file_id}` | Скачать файл по ID     |
| DELETE | `/files/{file_id}` | Удалить файл           |

### Profile

| Метод | URI        | Описание                               |
| ----- | ---------- | -------------------------------------- |
| GET   | `/profile` | Получить профиль текущего пользователя |
| POST  | `/profile` | Обновить профиль и установить аватар   |

## Работа с файлами

### Загрузка файла

Файл загружается через endpoint:

```text
POST /files
```

Формат запроса:

```text
multipart/form-data
```

Поле файла:

```text
file
```

Разрешённые MIME-типы для аватара:

```text
image/png
image/jpeg
image/jpg
```

Максимальный размер файла задаётся переменной окружения:

```env
MAX_FILE_SIZE=10485760
```

По умолчанию — 10 MB.

После загрузки файл сохраняется в MinIO, а в MongoDB сохраняются только его метаданные.

Пример ответа:

```json
{
  "id": "b38a39f6-b47f-4ddb-8fc6-4bc3899193c9",
  "original_name": "avatar.png",
  "size": 1400000,
  "mimetype": "image/png",
  "url": "/files/b38a39f6-b47f-4ddb-8fc6-4bc3899193c9"
}
```

### Скачивание файла

```text
GET /files/{file_id}
```

Файл отдаётся потоком через `StreamingResponse`.

При скачивании устанавливаются заголовки:

```text
Content-Type
Content-Disposition
Content-Length
```

### Удаление файла

```text
DELETE /files/{file_id}
```

При удалении выполняется:

* soft delete записи в MongoDB;
* удаление объекта из MinIO;
* инвалидация Redis-кеша метаданных файла.

## Redis-кеширование

Для метаданных файлов используется Redis.

Ключ кеша:

```text
wp:files:{fileId}:meta
```

TTL:

```text
300 секунд
```

При первом скачивании файла метаданные берутся из MongoDB и сохраняются в Redis. При повторном запросе метаданные берутся из кеша. При удалении файла кеш инвалидируется.

## Профиль и аватар

Профиль текущего пользователя можно получить через:

```text
GET /profile
```

Обновление профиля выполняется через:

```text
POST /profile
```

Пример запроса:

```json
{
  "display_name": "Сергей",
  "bio": "Lab 7 profile with MinIO avatar",
  "avatar_file_id": "b38a39f6-b47f-4ddb-8fc6-4bc3899193c9"
}
```

Перед установкой аватара backend проверяет, что файл существует, не удалён и принадлежит текущему пользователю.

Пример ответа:

```json
{
  "id": "6a1981d54abc0f43fdadacc9",
  "email": "user@example.com",
  "display_name": "Сергей",
  "bio": "Lab 7 profile with MinIO avatar",
  "avatar_file_id": "b38a39f6-b47f-4ddb-8fc6-4bc3899193c9",
  "avatar_url": "/files/b38a39f6-b47f-4ddb-8fc6-4bc3899193c9",
  "created_at": "2026-05-29T12:08:53.780000",
  "updated_at": "2026-05-29T21:47:16.226000"
}
```

## Проверка работы

### Проверить Swagger

```text
http://localhost:8000/api/docs
```

### Проверить MinIO

```text
http://localhost:9001
```

В bucket `wp-labs-files` должны появляться загруженные файлы.

### Проверить Redis-кеш

После вызова:

```text
GET /files/{file_id}
```

можно проверить ключ в Redis:

```bash
docker exec -it lab_redis redis-cli -a redis_secure_password_change_me
```

```redis
KEYS wp:files:*:meta
TTL wp:files:{fileId}:meta
```

## Выполненные требования лабораторной работы

* Добавлен MinIO в Docker Compose.
* Реализовано объектное хранение файлов.
* Файлы не хранятся в файловой системе приложения.
* Файлы не хранятся в MongoDB как BLOB.
* Метаданные файлов сохраняются в MongoDB.
* Реализована загрузка файлов через `multipart/form-data`.
* Реализовано скачивание файлов через stream.
* Реализована валидация MIME-type.
* Реализована валидация размера файла.
* Реализована проверка владельца файла.
* Реализован soft delete файла.
* Реализовано удаление объекта из MinIO.
* Реализовано Redis-кеширование метаданных файла.
* Реализована инвалидация кеша при удалении файла.
* Реализован профиль пользователя.
* Реализована установка аватара через `avatar_file_id`.
* Swagger отображает новые endpoints.
* Чувствительные данные вынесены в `.env`.
