# Project Structure

## Новая модульная архитектура FastAPI приложения

```
app/
├── main.py                          # Точка входа приложения, FastAPI app
├── schemas.py                       # Pydantic схемы для валидации
├── logger.py                        # Настройка логирования
├── db/
│   ├── __init__.py                  # Экспорт Base, engine, get_db
│   ├── database.py                  # Подключение к БД
│   └── models.py                    # SQLAlchemy модели
├── routers/
│   ├── __init__.py                  # Экспорт всех роутеров
│   ├── upload.py                    # Загрузка Excel файлов
│   ├── organizations.py             # CRUD операции с организациями
│   ├── organization_analytics.py    # Аналитика и редактирование организаций
│   ├── analytics.py                 # Общая аналитика системы
│   └── fns.py                       # API для работы с ФНС
├── services/
│   ├── __init__.py
│   ├── excel_processor_v2.py        # Обработка Excel файлов
│   ├── excel_exporter.py            # Экспорт в Excel
│   └── fns_api.py                   # Интеграция с ФНС API
├── dependencies/
│   ├── __init__.py
│   └── templates.py                 # Jinja2 templates dependency
├── templates/                       # HTML шаблоны
└── static/                          # Статические файлы (CSS, logo)
```

## Разделение обязанностей

### main.py (45 строк)
- Инициализация FastAPI приложения
- Подключение роутеров
- Настройка статических файлов
- Lifecycle events

### routers/upload.py (70 строк)
- GET /upload - страница загрузки
- POST /upload - обработка Excel файла

### routers/organizations.py (315 строк)
- GET /organizations - список с фильтрами
- GET /organizations/create - форма создания
- POST /organizations - создание организации
- GET /organizations/export - экспорт в Excel
- GET /organizations/{id} - детальный просмотр
- DELETE /organizations/{id} - удаление

### routers/organization_analytics.py (420 строк)
- GET /organizations/{id}/analytics - аналитика организации
- GET /organizations/{id}/edit - форма редактирования
- POST /organizations/{id}/edit-full - полное обновление данных
- POST /organizations/{id}/update-from-fns - обновление из ФНС
- POST /organizations/{id}/import-financials - импорт бухотчётности

### routers/analytics.py (330 строк)
- GET /analytics - общая аналитическая панель
- Фильтры по отраслям, годам, размеру, районам
- Графики и статистика

### routers/fns.py (50 строк)
- GET /api/fns/organization/{inn} - получение данных из ФНС

### schemas.py (35 строк)
- OrganizationCreate - схема для создания организации

## Преимущества новой структуры

✅ **Модульность**: Каждый роутер отвечает за свою область
✅ **Читаемость**: ~300-400 строк на файл вместо 1500
✅ **Масштабируемость**: Легко добавлять новые endpoints
✅ **Тестируемость**: Каждый модуль можно тестировать отдельно
✅ **Поддержка**: Быстрый поиск нужной функциональности
✅ **Чистота**: Минимум комментариев, понятный код

## Сравнение

- Старая структура: 1 файл, 1480 строк
- Новая структура: 8 файлов, 1286 строк (-13%)
- Средний размер файла: ~160 строк
- Максимальный файл: 420 строк (organization_analytics.py)

## Запуск

```bash
python app.py
```

Приложение автоматически импортирует `app.main:app`
