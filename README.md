# Индустриальные данные Москвы

Веб-приложение для анализа данных московских промышленных предприятий.

## Технологии

- **Backend**: FastAPI (модульная архитектура)
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy + Alembic
- **Frontend**: Jinja2 Templates, Chart.js
- **Logging**: structlog

## Структура проекта

```
app/
├── main.py                    # FastAPI приложение
├── schemas.py                 # Pydantic схемы
├── routers/                   # API endpoints
│   ├── upload.py              # Загрузка Excel
│   ├── organizations.py       # CRUD организаций
│   ├── organization_analytics.py  # Аналитика и редактирование
│   ├── analytics.py           # Общая аналитика
│   └── fns.py                 # Интеграция с ФНС
├── db/                        # База данных
│   ├── database.py            # Подключение
│   └── models.py              # SQLAlchemy модели
├── services/                  # Бизнес-логика
│   ├── excel_processor_v2.py  # Обработка Excel
│   ├── excel_exporter.py      # Экспорт в Excel
│   └── fns_api.py             # API ФНС
├── dependencies/              # DI зависимости
└── templates/                 # HTML шаблоны
```

## Быстрый старт

1. **Скопируйте .env файл**:
   ```bash
   cp .env.example .env
   ```

2. **Запустите PostgreSQL**:
   ```bash
   docker-compose up -d
   ```

3. **Установите зависимости**:
   ```bash
   poetry install
   ```

4. **Запустите приложение**:
   ```bash
   poetry run python app.py
   ```

5. **Откройте в браузере**:
   - Главная страница: http://localhost:8000
   - API документация: http://localhost:8000/docs

## Структура проекта

```
MosProm/
├── app/                  # Основное приложение
│   ├── crud.py          # CRUD операции
│   ├── database.py      # Подключение к БД
│   ├── models.py        # SQLAlchemy модели
│   ├── routes.py        # API endpoints
│   ├── schemas.py       # Pydantic схемы
│   ├── logger.py        # Логирование
│   ├── redis_client.py  # Redis клиент
│   └── templates/       # HTML шаблоны
├── alembic/             # Миграции БД
├── config.py            # Конфигурация
├── settings.toml        # Настройки приложения
├── docker-compose.yaml  # Docker конфигурация
└── app.py              # Точка входа
```

## API Endpoints

- `GET /` - Главная страница
- `GET /api/health` - Проверка здоровья сервиса
- `GET /api/organizations` - Список организаций (с пагинацией)
- `GET /api/organizations/{id}` - Детали организации
- `POST /api/organizations` - Создание организации
- `PUT /api/organizations/{id}` - Обновление организации
- `DELETE /api/organizations/{id}` - Удаление организации

## Разработка

**Форматирование кода**:
```bash
poetry run black .
```

**Проверка кода**:
```bash
poetry run flake8
```

**Создание миграции**:
```bash
poetry run alembic revision --autogenerate -m "description"
```

**Применение миграций**:
```bash
poetry run alembic upgrade head
```
