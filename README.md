# Индустриальные данные Москвы

Веб-приложение для анализа данных московских промышленных предприятий.

## Технологии

- **Backend**: FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Frontend**: Jinja2 Templates, Chart.js

## Быстрый старт

1. **Скопируйте .env файл**:
   ```bash
   cp .env.example .env
   ```
   Отредактируйте `.env` при необходимости.

2. **Запустите Docker контейнеры** (PostgreSQL + Redis):
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
