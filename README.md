# FastAPI CRUD Project (Lab 2)

## Описание

Проект представляет собой REST API, реализованный на FastAPI с использованием PostgreSQL и SQLAlchemy.

Реализованы основные операции:

* Создание (POST)
* Получение (GET)
* Обновление (PUT / PATCH)
* Удаление (Soft Delete)

Проект построен с соблюдением модульной архитектуры:

* routers (контроллеры)
* services (бизнес-логика)
* models (ORM)
* schemas (DTO)

---

## Технологии

* Python 3.11
* FastAPI
* SQLAlchemy
* PostgreSQL
* Alembic
* Uvicorn
* python-dotenv
* Docker / Docker Compose

---

## Запуск проекта

### Запуск через Docker (основной способ)

#### 1. Настроить `.env`

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните значения переменных окружения:

```env
DB_USER=student
DB_PASSWORD=your_password
DB_NAME=lab_db
DB_HOST=localhost
DB_PORT=5432
```

Для запуска через Docker используйте:

```env
DB_HOST=postgres
```

Примечание:
Файл `.env` не хранится в репозитории и используется только для локальной конфигурации.

#### 2. Запустить контейнеры

```bash
docker-compose up --build
```

#### 3. Применить миграции

```bash
alembic upgrade head
```

#### 4. Открыть Swagger

http://localhost:8000/docs

---

## Локальный запуск (для разработки)

#### 1. Клонировать проект

```bash
git clone <your-repo-url>
cd lab_2
```

#### 2. Создать виртуальное окружение

```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

#### 4. Настроить `.env`

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Заполните значения переменных окружения:

```env
DB_USER=student
DB_PASSWORD=your_password
DB_NAME=lab_db
DB_HOST=localhost
DB_PORT=5432
```

Для запуска через Docker используйте:

```env
DB_HOST=postgres
```

Примечание:
Файл `.env` не хранится в репозитории и используется только для локальной конфигурации.


#### 5. Применить миграции

```bash
alembic upgrade head
```

#### 6. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Swagger:
http://127.0.0.1:8000/docs

---

## Пример файла переменных окружения

См. файл `.env.example` в репозитории.

---

## Работа с базой данных

Миграции выполняются через Alembic:

```bash
alembic upgrade head
```

Ручное создание таблиц не используется.

---

## API эндпоинты

| Метод  | Endpoint    | Описание                       | Код ответа     |
| ------ | ----------- | ------------------------------ | -------------- |
| GET    | /items      | Получить список (с пагинацией) | 200 OK         |
| GET    | /items/{id} | Получить по ID                 | 200 OK         |
| POST   | /items      | Создать                        | 201 Created    |
| PUT    | /items/{id} | Полное обновление              | 200 OK         |
| PATCH  | /items/{id} | Частичное обновление           | 200 OK         |
| DELETE | /items/{id} | Soft delete                    | 204 No Content |

---

## Примеры запросов (cURL)

Создание ресурса:

```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Example Item", "description": "Test description"}'
```

Получение списка:

```bash
curl -X GET "http://localhost:8000/items?limit=2&offset=0"
```

Пример ответа:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Item 1",
      "description": "Description"
    }
  ],
  "meta": {
    "total": 3,
    "limit": 2,
    "offset": 0
  }
}
```

Удаление:

```bash
curl -X DELETE http://localhost:8000/items/1
```

Ответ:

```
204 No Content
```

---

## Особенности

### Soft Delete

Удаление не удаляет запись физически, а устанавливает поле:

```python
deleted_at = datetime.utcnow()
```

Удалённые записи не возвращаются в API.

---

### Pagination

Используется offset-based пагинация:

```
GET /items?limit=10&offset=0
```

Ответ содержит:

* data — список элементов
* meta — информация о пагинации (total, limit, offset)

---

### Переменные окружения

Конфигурация базы данных задаётся через `.env`:

```env
DB_USER=student
DB_PASSWORD=student
DB_NAME=lab_db
DB_HOST=localhost или postgres
DB_PORT=5432
```

---

## Проверка работы

1. Открыть Swagger:
   http://localhost:8000/docs

2. Выполнить:

* POST → создать item
* GET → проверить
* PATCH / PUT → обновить
* DELETE → удалить
* GET → убедиться, что item не отображается

---

## Проверка в pgAdmin

```sql
SELECT * FROM public.items ORDER BY id ASC;
```

Удалённые записи остаются в базе, но имеют заполненное поле deleted_at.

---

## Обработка ошибок

* 400 Bad Request — неверные данные
* 404 Not Found — ресурс не найден или удалён
* 409 Conflict — конфликт данных (например, дубликат)
* 500 Internal Server Error — внутренняя ошибка сервера

---

## Автор

Путинцев С.Р
090304-РПИб-о23
