# MosProm

Веб-приложение для анализа промышленных предприятий Москвы с инструментами управления данными организаций, аналитики финансовых показателей, загрузки данных из Excel и интеграции с ФНС.

---

## Запуск

### Предварительные требования

- Python 3.11+
- Poetry
- Docker

### 1. Установка зависимостей
```bash
poetry install
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта шаблон - .env.example (апи ключ для [фнс апи](https://api-fns.ru/index) нужно сделать свой, т.к. там привязка к одному ip):

```env
POSTGRES_USER=mosprom_user
POSTGRES_PASSWORD=mosprom_password
POSTGRES_DB=mosprom_db
DATABASE_URL=postgresql://mosprom_user:mosprom_password@localhost:5432/mosprom_db
SECRET_KEY=your-secret-key-here
DEBUG=true
```

### 3. Настройка базы данных
```bash
docker-compose up -d
```

### 4. Применение миграций

```bash
poetry run alembic upgrade head
```

### 5. Запуск приложения

```bash
poetry run python app.py
```

Приложение будет доступно по адресу: **http://localhost:8000**

---

## Технологии

### Backend
- **FastAPI** 0.109+ - Веб-фреймворк
- **SQLAlchemy** 2.0+ - ORM для работы с БД
- **Pydantic** 2.5+ - Валидация данных
- **Alembic** 1.13+ - Миграции БД
- **Uvicorn** - ASGI сервер

### Database
- **PostgreSQL** 16 - Реляционная БД

### Frontend
- **Jinja2** - Шаблонизатор HTML
- **Bootstrap** - CSS фреймворк
- **Chart.js** - Графики и визуализация

### Остальное
- **openpyxl** - Работа с Excel
- **httpx** - HTTP клиент

### Конфигурация
- **Dynaconf** - Управление конфигурацией
- **structlog** - Структурированное логирование

---


## Структура проекта

```
app/
├── main.py              # Точка входа FastAPI
├── schemas.py           # Pydantic модели
├── logger.py            # Настройка логирования
├── db/                  # База данных
│   ├── database.py      # SQLAlchemy engine
│   └── models.py        # ORM модели
├── routers/             # API endpoints
├── services/            # Бизнес-логика
├── templates/           # HTML шаблоны
└── static/              # CSS, JS, изображения

alembic/                 # Миграции БД
config.py               # Конфигурация Dynaconf
settings.toml           # Настройки приложения
docker-compose.yaml     # PostgreSQL контейнер
```

