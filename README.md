# FastAPI CRUD Project (Lab 2)

## Описание

Этот проект представляет собой REST API, реализованный на FastAPI, с использованием PostgreSQL и SQLAlchemy.

Реализованы основные операции:

* Создание (POST)
* Получение (GET)
* Обновление (PUT / PATCH)
* Удаление (Soft Delete)

---

## Технологии

* Python 3.11
* FastAPI
* SQLAlchemy
* PostgreSQL
* Alembic
* Uvicorn
* python-dotenv

---

## Установка и запуск

### 1. Клонировать проект

```bash
git clone <your-repo-url>
cd lab_2
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить .env

Создай файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql://student:student@localhost:5432/lab_db
```

---

### 5. Запустить сервер

```bash
uvicorn app.main:app --reload
```

Swagger будет доступен по адресу:
http://127.0.0.1:8000/docs

---

## Работа с базой данных

### Применение миграций

```bash
alembic upgrade head
```

---

## API эндпоинты

### 🔹 Создать item

POST `/items`

```json
{
  "name": "Test item",
  "description": "Description"
}
```

---

### 🔹 Получить все items (с пагинацией)

GET `/items?limit=10&offset=0`

---

### 🔹 Получить item по ID

GET `/items/{id}`

---

### 🔹 Полное обновление

PUT `/items/{id}`

```json
{
  "name": "Updated",
  "description": "Full update"
}
```

---

### 🔹 Частичное обновление

PATCH `/items/{id}`

```json
{
  "name": "Only name updated"
}
```

---

### 🔹 Удаление (Soft Delete)

DELETE `/items/{id}`

---

## Особенности

### Soft Delete

Удаление не удаляет запись из БД, а устанавливает поле:

```python
deleted_at = datetime.utcnow()
```

### Pagination

Реализована через параметры:

* `limit`
* `offset`

### .env конфигурация

Строка подключения к БД хранится в `.env`, а не в коде.

---

## Проверка работы

1. Открыть Swagger:
   http://127.0.0.1:8000/docs

2. Последовательно:

   * POST → создать item
   * GET → проверить
   * PATCH / PUT → обновить
   * DELETE → удалить
   * GET → убедиться, что item скрыт

---

## Проверка в pgAdmin

```sql
SELECT * FROM public.items ORDER BY id ASC;
```

---

## 👨‍💻 Автор

Путинцев С.Р 090304-РПИб-о23
