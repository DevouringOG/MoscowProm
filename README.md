# 🏭 MosProm - Industrial Data Moscow

Веб-приложение для анализа промышленных предприятий Москвы. Система предоставляет инструменты для управления данными организаций, аналитики финансовых показателей, загрузки данных из Excel и интеграции с ФНС.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Технологический стек](#-технологический-стек)
- [Архитектура](#-архитектура)
- [Установка и запуск](#-установка-и-запуск)
- [Структура базы данных](#-структура-базы-данных)
- [API Endpoints](#-api-endpoints)
- [Конфигурация](#-конфигурация)
- [Разработка](#-разработка)
- [Миграции базы данных](#-миграции-базы-данных)
- [Логирование](#-логирование)

---

## 🚀 Возможности

### 📊 Аналитическая панель
- **Общая статистика**: Количество организаций, выручка, численность, инвестиции
- **Динамика по годам**: Графики изменения ключевых показателей
- **Фильтрация**: По отраслям, размеру компании, районам, временным периодам
- **Топ-списки**: Лидеры по выручке, налогам, численности, инвестициям
- **Экспорт**: По районам и отраслям промышленности

### 🏢 Управление организациями
- **Просмотр списка**: Пагинация (20 записей на страницу)
- **Поиск**: По названию и ИНН
- **Фильтрация**: Отрасль, район, регион, размер компании
- **Сортировка**: По любому полю (название, ИНН, отрасль, район и т.д.)
- **CRUD операции**: Создание, просмотр, редактирование, удаление
- **Экспорт**: Выгрузка данных в Excel

### 📈 Детальная аналитика организации
- **Карточка организации**: Полная информация о компании
- **Финансовые показатели**: Выручка, прибыль, налоги по годам
- **HR-метрики**: Численность, ФОТ, средняя зарплата
- **Графики трендов**: Динамика показателей за несколько лет
- **Сравнение с предыдущим годом**: Процентные изменения
- **Географические данные**: Адреса и координаты площадок

### 📤 Загрузка данных
- **Импорт из Excel**: Массовая загрузка данных организаций
- **Валидация**: Проверка формата и целостности данных
- **Автоматическое обновление**: Обновление существующих записей при совпадении ИНН
- **Поддержка временных рядов**: 
  - Финансовые показатели (выручка, прибыль) за 2017-2023
  - Налоговые данные за 2017-2024
  - Инвестиции за 2021-2023
  - Экспорт за 2019-2023

### 🔌 Интеграция с ФНС
- **Автозаполнение формы**: Получение данных организации по ИНН
- **API api-fns.ru**: Запрос основной информации из ЕГРЮЛ/ЕГРИП
- **Бухгалтерская отчетность**: Получение финансовых показателей (формы 1-4)

### ✏️ Редактирование данных
- **Основная информация**: Редактирование базовых данных организации
- **Полное редактирование**: 
  - Финансовые показатели по годам
  - Налоговые отчисления
  - Активы (земля, здания)
  - Продукция
  - Метаинформация

---

## 🛠 Технологический стек

### Backend
- **FastAPI** `0.109+` - Современный высокопроизводительный веб-фреймворк
- **SQLAlchemy** `2.0+` - ORM для работы с базой данных
- **Pydantic** `2.5+` - Валидация данных и настроек
- **Alembic** `1.13+` - Миграции базы данных
- **Uvicorn** - ASGI сервер с поддержкой hot-reload

### Database
- **PostgreSQL** `16` - Реляционная база данных
- **psycopg2-binary** - PostgreSQL адаптер для Python

### Frontend
- **Jinja2** - Шаблонизатор для HTML
- **Bootstrap** - CSS фреймворк (через CDN)
- **Chart.js** - Библиотека для графиков
- Нативный JavaScript (без фреймворков)

### Data Processing
- **openpyxl** - Работа с Excel файлами (.xlsx)
- **pandas** - Анализ и обработка данных
- **httpx** - HTTP клиент для асинхронных запросов

### Configuration & Logging
- **Dynaconf** - Управление конфигурацией и окружениями
- **structlog** - Структурированное логирование (JSON)

### Development Tools
- **Poetry** - Управление зависимостями и виртуальным окружением
- **Black** - Форматирование кода (line-length=79)
- **Flake8** - Линтинг кода
- **Docker Compose** - Контейнеризация PostgreSQL

---

## 🏗 Архитектура

Проект следует модульной архитектуре FastAPI с разделением ответственности:

```
app/
├── main.py                  # Точка входа FastAPI приложения
├── schemas.py              # Pydantic модели для валидации
├── logger.py               # Настройка structlog
│
├── db/                     # Database layer
│   ├── database.py         # SQLAlchemy engine и session
│   └── models.py           # ORM модели (6 таблиц)
│
├── routers/                # API endpoints (роутеры)
│   ├── organizations.py            # CRUD организаций
│   ├── organization_analytics.py   # Детальная аналитика
│   ├── analytics.py                # Общая панель аналитики
│   ├── upload.py                   # Загрузка Excel
│   └── fns.py                      # API ФНС
│
├── services/               # Business logic
│   ├── excel_processor_v2.py   # Обработка Excel файлов
│   ├── excel_exporter.py       # Экспорт в Excel
│   └── fns_api.py             # Интеграция с ФНС
│
├── dependencies/           # FastAPI dependencies
│   └── templates.py        # Jinja2 templates
│
├── templates/              # HTML шаблоны
│   ├── index.html
│   ├── analytics.html
│   ├── organizations.html
│   ├── organization_detail.html
│   ├── organization_edit.html
│   ├── organization_edit_full.html
│   ├── organization_analytics.html
│   └── upload.html
│
└── static/                 # Статические файлы
    └── css/                # CSS стили

alembic/                    # Миграции БД
├── versions/               # Файлы миграций
├── env.py                 # Конфигурация Alembic
└── script.py.mako         # Шаблон миграций

config.py                   # Dynaconf конфигурация
settings.toml              # Настройки приложения
.env                       # Переменные окружения
docker-compose.yaml        # PostgreSQL контейнер
```

### Принципы архитектуры:

1. **Separation of Concerns**: Разделение роутеров, сервисов, моделей
2. **Dependency Injection**: Использование FastAPI Depends
3. **Repository Pattern**: Работа с БД через SQLAlchemy ORM
4. **Configuration Management**: Dynaconf для окружений
5. **Structured Logging**: JSON логи через structlog
6. **Database Migrations**: Alembic для версионирования схемы

---

## 📦 Установка и запуск

### Предварительные требования

- Python 3.11+
- Poetry
- PostgreSQL 16+ (или Docker)
- Git

### 1. Клонирование репозитория

```bash
git clone https://github.com/yourusername/mosprom.git
cd mosprom
```

### 2. Установка зависимостей

```bash
# Установка Poetry (если еще не установлен)
curl -sSL https://install.python-poetry.org | python3 -

# Установка зависимостей проекта
poetry install
```

### 3. Настройка базы данных

#### Вариант A: Использование Docker (рекомендуется)

```bash
# Запуск PostgreSQL в контейнере
docker-compose up -d

# Проверка статуса
docker-compose ps
```

#### Вариант B: Локальный PostgreSQL

```bash
# Создание базы данных
createdb mosprom_db

# Создание пользователя (опционально)
psql -c "CREATE USER mosprom_user WITH PASSWORD 'mosprom_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE mosprom_db TO mosprom_user;"
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Database
POSTGRES_USER=mosprom_user
POSTGRES_PASSWORD=mosprom_password
POSTGRES_DB=mosprom_db
DATABASE_URL=postgresql://mosprom_user:mosprom_password@localhost:5432/mosprom_db

# Application
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=true

# FNS API (опционально)
FNS_API_KEY=your-fns-api-key
```

### 5. Применение миграций

```bash
# Применить все миграции
poetry run alembic upgrade head
```

### 6. Запуск приложения

```bash
# Режим разработки с hot-reload
poetry run python app.py

# Или через uvicorn напрямую
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: **http://localhost:8000**

### 7. Проверка работы

- **Главная страница**: http://localhost:8000
- **Аналитика**: http://localhost:8000/analytics
- **Список организаций**: http://localhost:8000/organizations
- **Загрузка данных**: http://localhost:8000/upload

---

## 🗄 Структура базы данных

### ER-диаграмма

```
organizations (основная таблица)
    ├── organization_metrics (финансовые показатели по годам)
    ├── organization_taxes (налоги по годам)
    ├── organization_assets (активы: земля, здания)
    ├── organization_products (продукция)
    └── organization_meta (метаинформация)
```

### Таблица: `organizations`

**Основная информация о промышленных предприятиях**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | PRIMARY KEY |
| `inn` | String(12) | ИНН (уникальный, индекс) |
| `name` | String(500) | Краткое наименование |
| `full_name` | String(1000) | Полное наименование |
| `status_spark` | String(200) | Статус из СПАРК |
| `status_internal` | String(200) | Внутренний статус |
| `status_final` | String(200) | Итоговый статус |
| `date_added` | DateTime | Дата добавления |
| `legal_address` | String(1000) | Юридический адрес |
| `production_address` | String(1000) | Адрес производства |
| `additional_address` | String(1000) | Дополнительная площадка |
| `main_industry` | String(200) | Основная отрасль |
| `main_subindustry` | String(200) | Основная подотрасль |
| `extra_industry` | String(200) | Дополнительная отрасль |
| `extra_subindustry` | String(200) | Дополнительная подотрасль |
| `main_okved` | String(100) | Основной ОКВЭД |
| `main_okved_name` | String(200) | Название ОКВЭД |
| `prod_okved` | String(100) | Производственный ОКВЭД |
| `prod_okved_name` | String(200) | Название произв. ОКВЭД |
| `company_info` | Text | Информация о компании |
| `company_size` | String(100) | Размер компании (текущий) |
| `company_size_2022` | String(100) | Размер компании 2022 |
| `size_by_employees` | String(100) | Размер по численности |
| `size_by_employees_2022` | String(100) | Размер по численности 2022 |
| `size_by_revenue` | String(100) | Размер по выручке |
| `size_by_revenue_2022` | String(100) | Размер по выручке 2022 |
| `registration_date` | DateTime | Дата регистрации |
| `head_name` | String(200) | ФИО руководителя |
| `parent_org_name` | String(500) | Головная организация |
| `parent_org_inn` | String(12) | ИНН головной организации |
| `parent_relation_type` | String(200) | Тип связи с головной |
| `head_contacts` | String(500) | Контакты руководителя |
| `head_email` | String(200) | Email руководителя |
| `employee_contact` | String(500) | Контакты сотрудника |
| `phone` | String(100) | Телефон |
| `emergency_contact` | String(500) | Экстренный контакт |
| `website` | String(300) | Веб-сайт |
| `email` | String(200) | Email компании |
| `support_data` | Text | Данные по поддержке |
| `special_status` | String(200) | Особый статус |
| `site_final` | String(200) | Итоговая площадка |
| `got_moscow_support` | Boolean | Получала поддержку Москвы |
| `is_system_critical` | Boolean | Системообразующее |
| `msp_status` | String(100) | Статус МСП |
| `coordinates_lat` | Float | Широта |
| `coordinates_lon` | Float | Долгота |
| `legal_address_coords` | String(200) | Координаты юр. адреса |
| `production_address_coords` | String(200) | Координаты производства |
| `additional_address_coords` | String(200) | Координаты доп. площадки |
| `district` | String(200) | Округ Москвы |
| `region` | String(200) | Регион |
| `created_at` | DateTime | Время создания записи |
| `updated_at` | DateTime | Время обновления записи |

### Таблица: `organization_metrics`

**Временные ряды финансовых и HR метрик по годам**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | PRIMARY KEY |
| `organization_id` | Integer | FOREIGN KEY → organizations.id |
| `year` | Integer | Год (индекс) |
| `revenue` | Float | Выручка (руб.) |
| `profit` | Float | Прибыль (руб.) |
| `total_employees` | Integer | Численность всего |
| `moscow_employees` | Integer | Численность Москва |
| `total_fot` | Float | ФОТ всего (руб.) |
| `moscow_fot` | Float | ФОТ Москва (руб.) |
| `avg_salary_total` | Float | Средняя ЗП всего |
| `avg_salary_moscow` | Float | Средняя ЗП Москва |
| `investments` | Float | Инвестиции (руб.) |
| `export_volume` | Float | Объем экспорта (руб.) |
| `created_at` | DateTime | Время создания |
| `updated_at` | DateTime | Время обновления |

**Индекс**: `(organization_id, year)` - составной индекс для быстрых запросов

### Таблица: `organization_taxes`

**Налоговые отчисления по годам**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | PRIMARY KEY |
| `organization_id` | Integer | FOREIGN KEY → organizations.id |
| `year` | Integer | Год (индекс) |
| `total_taxes_moscow` | Float | Всего налогов в Москве |
| `profit_tax` | Float | Налог на прибыль |
| `property_tax` | Float | Налог на имущество |
| `land_tax` | Float | Земельный налог |
| `ndfl` | Float | НДФЛ |
| `transport_tax` | Float | Транспортный налог |
| `other_taxes` | Float | Прочие налоги |
| `excise` | Float | Акцизы |

### Таблица: `organization_assets`

**Активы организации (недвижимость)**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | PRIMARY KEY |
| `organization_id` | Integer | FOREIGN KEY → organizations.id |
| `cadastral_number_land` | String(200) | Кадастровый номер земли |
| `land_area` | Float | Площадь земли (кв.м) |
| `land_usage` | String(200) | Использование земли |
| `land_ownership_type` | String(200) | Тип собственности земли |
| `land_owner` | String(500) | Собственник земли |
| `cadastral_number_building` | String(200) | Кадастровый номер здания |
| `building_area` | Float | Площадь здания (кв.м) |
| `building_usage` | String(200) | Использование здания |
| `building_type` | String(200) | Тип здания |
| `building_purpose` | String(200) | Назначение здания |
| `building_ownership_type` | String(200) | Тип собственности здания |
| `building_owner` | String(500) | Собственник здания |
| `production_area` | Float | Производственная площадь |
| `property_summary` | Text | Общая информация об активах |

### Таблица: `organization_products`

**Продукция организации**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | PRIMARY KEY |
| `organization_id` | Integer | FOREIGN KEY → organizations.id |
| `product_name` | String(500) | Название продукции |
| `standardized_product` | String(500) | Стандартизированное название |
| `okpd2_codes` | String(500) | Коды ОКПД2 |
| `product_types` | String(500) | Типы продукции |
| `product_catalog` | String(500) | Каталог продукции |
| `has_government_orders` | Boolean | Наличие гос. заказов |
| `capacity_usage` | String(200) | Загрузка мощностей |
| `has_export` | Boolean | Экспортирует |
| `export_volume_last_year` | Float | Объем экспорта за прошлый год |
| `export_countries` | String(1000) | Страны экспорта |
| `tnved_code` | String(100) | Код ТН ВЭД |

### Таблица: `organization_meta`

**Метаинформация и дополнительные данные**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | Integer | PRIMARY KEY |
| `organization_id` | Integer | FOREIGN KEY → organizations.id |
| `industry_spark` | String(500) | Отрасль из СПАРК |
| `industry_directory` | String(500) | Отрасль из справочника |
| `presentation_links` | String(1000) | Ссылки на презентации |
| `registry_development` | Text | Реестры развития |
| `other_notes` | Text | Прочие примечания |

### Связи между таблицами

- `organizations` ← **1:N** → `organization_metrics`
- `organizations` ← **1:N** → `organization_taxes`
- `organizations` ← **1:1** → `organization_assets`
- `organizations` ← **1:N** → `organization_products`
- `organizations` ← **1:1** → `organization_meta`

Все связи используют `CASCADE DELETE` - при удалении организации удаляются все связанные данные.

---

## 🔌 API Endpoints

### 📊 Аналитика

#### `GET /analytics`
**Общая панель аналитики**

**Query Parameters:**
- `industries` (list[str]) - Фильтр по отраслям
- `year_from` (int) - Начальный год
- `year_to` (int) - Конечный год
- `company_sizes` (list[str]) - Фильтр по размеру компании
- `districts` (list[str]) - Фильтр по округам

**Response:** HTML страница с аналитикой

**Возвращаемые данные:**
- Общая статистика (организации, выручка, сотрудники, инвестиции, экспорт, налоги)
- Графики динамики по годам
- Топ-10 компаний по различным показателям
- Распределение по округам и отраслям

---

### 🏢 Организации

#### `GET /organizations`
**Список организаций с фильтрацией**

**Query Parameters:**
- `page` (int, default=1) - Номер страницы
- `search` (str) - Поиск по названию или ИНН
- `industry` (list[str]) - Фильтр по отраслям
- `district` (list[str]) - Фильтр по округам
- `region` (list[str]) - Фильтр по регионам
- `size` (list[str]) - Фильтр по размеру компании
- `sort_by` (str, default="name") - Поле сортировки
- `order` (str, default="asc") - Направление сортировки (asc/desc)

**Response:** HTML страница со списком организаций (20 на странице)

---

#### `GET /organizations/{organization_id}`
**Детальная информация об организации**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Response:** HTML страница с полной карточкой организации

---

#### `GET /organizations/{organization_id}/analytics`
**Аналитика конкретной организации**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Response:** HTML страница с графиками и трендами

**Возвращаемые данные:**
- Основная информация
- Финансовые показатели по годам (выручка, прибыль)
- HR метрики (численность, ФОТ, средняя ЗП)
- Налоговые отчисления
- Инвестиции и экспорт
- Сравнение с предыдущим годом (тренды)

---

#### `GET /organizations/{organization_id}/edit`
**Форма редактирования основных данных**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Response:** HTML форма для редактирования

---

#### `POST /organizations/{organization_id}/edit`
**Сохранение изменений основных данных**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Form Data:**
- Все поля из `OrganizationCreate` schema

**Response:** Redirect на `/organizations/{organization_id}`

---

#### `GET /organizations/{organization_id}/edit-full`
**Форма полного редактирования**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Response:** HTML форма с редактированием всех связанных данных

---

#### `POST /organizations/{organization_id}/edit-full`
**Сохранение полного редактирования**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Form Data:**
- Основные данные организации
- Финансовые показатели по годам (JSON)
- Налоговые данные по годам (JSON)
- Активы (JSON)
- Продукция (JSON)
- Метаинформация (JSON)

**Response:** Redirect на `/organizations/{organization_id}/analytics`

---

#### `GET /organizations/new`
**Форма создания новой организации**

**Response:** HTML форма создания

---

#### `POST /organizations`
**Создание новой организации**

**Form Data:**
- Поля из `OrganizationCreate` schema

**Response:** Redirect на страницу созданной организации

---

#### `POST /organizations/{organization_id}/delete`
**Удаление организации**

**Path Parameters:**
- `organization_id` (int) - ID организации

**Response:** Redirect на `/organizations`

---

#### `GET /organizations/export`
**Экспорт организаций в Excel**

**Query Parameters:**
- `search` (str) - Поиск по названию или ИНН
- `industry` (list[str]) - Фильтр по отраслям
- `district` (list[str]) - Фильтр по округам
- `region` (list[str]) - Фильтр по регионам
- `size` (list[str]) - Фильтр по размеру компании

**Response:** Excel файл (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

---

### 📤 Загрузка данных

#### `GET /upload`
**Страница загрузки Excel файлов**

**Response:** HTML форма загрузки

---

#### `POST /upload`
**Загрузка и обработка Excel файла**

**Form Data:**
- `file` (UploadFile) - Excel файл (.xlsx или .xls)

**Response:** JSON с результатами обработки

```json
{
  "organizations_new": 150,
  "organizations_updated": 45,
  "rows_processed": 195,
  "rows_skipped": 5,
  "errors": [],
  "organizations_details": [
    {
      "inn": "1234567890",
      "name": "ООО Пример",
      "action": "created"
    }
  ]
}
```

**Формат Excel файла:**
- Столбец 1 (B): ИНН
- Столбец 2 (C): Наименование организации
- Столбцы 47-53: Выручка 2017-2023
- Столбцы 54-60: Прибыль 2017-2023
- Столбцы 61-67: Численность всего 2017-2023
- Столбцы 68-74: Численность Москва 2017-2023
- Столбцы 75-81: ФОТ всего 2017-2023
- Столбцы 82-88: ФОТ Москва 2017-2023
- Столбцы 89-95: Средняя ЗП всего 2017-2023
- Столбцы 96-102: Средняя ЗП Москва 2017-2023
- Столбцы 103-110: Налоги всего 2017-2024
- Столбцы 111-158: Детализация налогов
- Столбцы 167-169: Инвестиции 2021-2023
- Столбцы 170-174: Экспорт 2019-2023

**Error Handling:**
- Дублирование ИНН - обновление существующей записи
- Отсутствие ИНН - пропуск строки
- Невалидные данные - детальное сообщение об ошибке

---

### 🔌 Интеграция с ФНС

#### `GET /api/fns/organization/{inn}`
**Получение данных организации из ФНС**

**Path Parameters:**
- `inn` (str) - ИНН (10 или 12 цифр)

**Response:** JSON с данными организации

```json
{
  "status": "success",
  "data": {
    "inn": "1234567890",
    "name": "ООО ПРИМЕР",
    "full_name": "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ПРИМЕР\"",
    "kpp": "123456789",
    "ogrn": "1234567890123",
    "registration_date": "2010-01-15",
    "legal_address": "г Москва, ул Примерная, д 1",
    "okved": "12.34",
    "okved_name": "Производство примерных изделий",
    "head_name": "Иванов Иван Иванович",
    "status": "Действующее"
  }
}
```

**Error Codes:**
- `400` - Невалидный формат ИНН
- `404` - Организация не найдена в ФНС
- `503` - API ФНС отключено или не настроено

---

## ⚙️ Конфигурация

### Файл `settings.toml`

```toml
[default]
app_name = "Industrial Data Moscow"
app_version = "0.1.0"
debug = true
host = "0.0.0.0"
port = 8000

[default.database]
host = "localhost"
port = 5432
name = "mosprom_db"
user = "mosprom_user"
password = "mosprom_password"
echo = false              # Логирование SQL запросов
pool_size = 5            # Размер пула соединений
max_overflow = 10        # Максимум дополнительных соединений

[default.logging]
level = "INFO"           # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_dir = "logs"
log_file = "mosprom.log"
log_format = "json"      # json или text
log_to_console = true
log_to_file = true

[default.upload]
max_file_size = 10485760    # 10 MB
allowed_extensions = [".xlsx", ".xls"]
upload_dir = "uploads"

[default.pagination]
default_page_size = 50
max_page_size = 1000

[default.fns_api]
api_key = "your-api-key-here"
enabled = true
timeout = 30

# Production окружение
[production]
debug = false

[production.logging]
level = "WARNING"

# Development окружение
[development]
debug = true

[development.database]
echo = true    # Включить логирование SQL в режиме разработки
```

### Переменные окружения (`.env`)

```bash
# Database credentials
POSTGRES_USER=mosprom_user
POSTGRES_PASSWORD=mosprom_password
POSTGRES_DB=mosprom_db
DATABASE_URL=postgresql://mosprom_user:mosprom_password@localhost:5432/mosprom_db

# Application
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=true

# FNS API (получить на https://api-fns.ru)
FNS_API_KEY=your-fns-api-key

# Environment (development, production)
MOSPROM_ENV=development
```

### Переключение окружений

```bash
# Development (по умолчанию)
export MOSPROM_ENV=development
poetry run python app.py

# Production
export MOSPROM_ENV=production
poetry run python app.py
```

---

## 👨‍💻 Разработка

### Установка инструментов разработки

```bash
# Установка dev зависимостей
poetry install --with dev

# Black (форматирование кода)
poetry run black .

# Flake8 (линтинг)
poetry run flake8 .
```

### Настройки Code Style

**Black:**
- Line length: **79** символов (PEP 8)
- Target version: Python 3.11+

**Flake8:**
- Max line length: 79
- Игнорируемые правила: E203, W503

### Pre-commit хуки (рекомендуется)

```bash
# Установка pre-commit
pip install pre-commit

# Установка хуков
pre-commit install

# Запуск вручную
pre-commit run --all-files
```

### Создание новой миграции

```bash
# Автогенерация миграции
poetry run alembic revision --autogenerate -m "Add new column to organizations"

# Применение миграции
poetry run alembic upgrade head

# Откат последней миграции
poetry run alembic downgrade -1

# Просмотр истории миграций
poetry run alembic history
```

### Структура нового роутера

```python
# app/routers/example.py
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.dependencies.templates import templates
from app.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/example", tags=["example"])

@router.get("/")
async def example_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    logger.info("example_endpoint_called")
    return templates.TemplateResponse(
        "example.html",
        {"request": request}
    )
```

Зарегистрировать в `app/main.py`:

```python
from app.routers import example

app.include_router(example.router)
```

### Добавление нового сервиса

```python
# app/services/example_service.py
from app.logger import get_logger

logger = get_logger(__name__)

class ExampleService:
    def __init__(self):
        pass
    
    def do_something(self):
        logger.info("doing_something")
        return "result"

def get_example_service():
    return ExampleService()
```

---

## 🗄 Миграции базы данных

### Команды Alembic

```bash
# Создать новую миграцию (автоматически)
poetry run alembic revision --autogenerate -m "Description of changes"

# Создать пустую миграцию (вручную)
poetry run alembic revision -m "Description"

# Применить все миграции
poetry run alembic upgrade head

# Применить конкретную миграцию
poetry run alembic upgrade <revision_id>

# Откатить одну миграцию
poetry run alembic downgrade -1

# Откатить к конкретной миграции
poetry run alembic downgrade <revision_id>

# Откатить все миграции
poetry run alembic downgrade base

# Показать текущую версию БД
poetry run alembic current

# Показать историю миграций
poetry run alembic history

# Показать SQL без применения
poetry run alembic upgrade head --sql
```

### Пример миграции

```python
"""Add email column to organizations

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-10-19 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        'organizations',
        sa.Column('email', sa.String(200), nullable=True)
    )
    op.create_index(
        'ix_organizations_email',
        'organizations',
        ['email']
    )

def downgrade():
    op.drop_index('ix_organizations_email', table_name='organizations')
    op.drop_column('organizations', 'email')
```

### Добавление модели в Alembic

После создания новой модели в `app/db/models.py`, модель автоматически будет обнаружена Alembic благодаря импорту в `alembic/env.py`:

```python
# alembic/env.py
from app.db.database import Base
from app.db import models  # Импортирует все модели

target_metadata = Base.metadata
```

---

## 📝 Логирование

### Структурированное логирование (structlog)

Приложение использует **structlog** для структурированного логирования в формате JSON.

### Настройка логирования

```python
# app/logger.py
import structlog
import logging

def setup_logging():
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str):
    return structlog.get_logger(name)
```

### Использование логгера

```python
from app.logger import get_logger

logger = get_logger(__name__)

# Информационное сообщение
logger.info("user_action", user_id=123, action="create_organization")

# Сообщение с дополнительным контекстом
logger.info(
    "organization_created",
    organization_id=456,
    inn="1234567890",
    name="ООО Пример"
)

# Ошибка
logger.error(
    "database_error",
    error=str(e),
    query="SELECT * FROM organizations"
)

# Предупреждение
logger.warning(
    "slow_query",
    duration_ms=5000,
    query="Complex aggregation"
)
```

### Формат логов

**JSON (production):**
```json
{
  "event": "organization_created",
  "organization_id": 456,
  "inn": "1234567890",
  "name": "ООО Пример",
  "level": "info",
  "logger": "app.routers.organizations",
  "timestamp": "2025-10-19T12:00:00.123456Z"
}
```

**Console (development):**
```
2025-10-19 12:00:00 [info     ] organization_created       [app.routers.organizations] organization_id=456 inn=1234567890 name=ООО Пример
```

### Файлы логов

Логи сохраняются в директорию `logs/`:
- `logs/mosprom.log` - все логи приложения

Настройка в `settings.toml`:
```toml
[default.logging]
log_dir = "logs"
log_file = "mosprom.log"
log_to_console = true
log_to_file = true
```

---

## 🐳 Docker

### Docker Compose

Проект включает `docker-compose.yaml` для запуска PostgreSQL:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: mosprom_postgres
    env_file: [.env]
    environment:
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Команды Docker

```bash
# Запуск контейнера
docker-compose up -d

# Остановка контейнера
docker-compose down

# Просмотр логов
docker-compose logs -f postgres

# Проверка статуса
docker-compose ps

# Подключение к PostgreSQL
docker-compose exec postgres psql -U mosprom_user -d mosprom_db

# Перезапуск контейнера
docker-compose restart postgres

# Удаление данных (осторожно!)
docker-compose down -v
```

### Backup и Restore

```bash
# Создание бэкапа
docker-compose exec -T postgres pg_dump -U mosprom_user mosprom_db > backup.sql

# Восстановление из бэкапа
docker-compose exec -T postgres psql -U mosprom_user mosprom_db < backup.sql
```

---

## 📊 Производительность

### Оптимизация запросов

1. **Индексы**: На часто используемые поля (`inn`, `name`, `main_industry`)
2. **Составной индекс**: `(organization_id, year)` для метрик
3. **Пагинация**: Ограничение 20 записей на страницу
4. **Lazy loading**: Связанные данные загружаются только при необходимости

### Connection Pooling

SQLAlchemy использует пул соединений:
```toml
[default.database]
pool_size = 5          # Размер пула
max_overflow = 10      # Дополнительные соединения
```

### Кэширование (будущее улучшение)

Возможные точки кэширования:
- Список отраслей, округов (для фильтров)
- Агрегированная статистика (обновление раз в час)
- Результаты сложных запросов

---

## 🔒 Безопасность

### Текущие меры безопасности

1. **SQL Injection**: Использование SQLAlchemy ORM (параметризованные запросы)
2. **XSS**: Jinja2 автоматически экранирует HTML
3. **File Upload**: Валидация расширений файлов (.xlsx, .xls)
4. **Database**: Хранение credentials в `.env` (не в коде)

### Рекомендации для production

1. **HTTPS**: Использовать reverse proxy (nginx) с SSL
2. **Аутентификация**: Добавить OAuth2/JWT для защиты API
3. **Rate Limiting**: Ограничение количества запросов
4. **CORS**: Настроить CORS для API endpoints
5. **Secrets**: Использовать secrets manager (AWS Secrets Manager, Vault)
6. **Database**: Регулярные бэкапы и шифрование
7. **Logging**: Не логировать чувствительные данные (пароли, токены)

---

## 🧪 Тестирование

### Структура тестов (планируется)

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── test_models.py          # Тесты моделей
├── test_services.py        # Тесты бизнес-логики
├── test_routers.py         # Тесты API endpoints
└── test_integration.py     # Интеграционные тесты
```

### Запуск тестов

```bash
# Установка pytest
poetry add --group dev pytest pytest-asyncio pytest-cov httpx

# Запуск всех тестов
poetry run pytest

# С покрытием кода
poetry run pytest --cov=app --cov-report=html

# Конкретный тест
poetry run pytest tests/test_models.py::test_organization_creation
```

---

## 📈 Roadmap

### Ближайшие улучшения

- [ ] Добавить аутентификацию и авторизацию
- [ ] Внедрить Redis для кэширования
- [ ] REST API с документацией OpenAPI (Swagger)
- [ ] GraphQL endpoint
- [ ] Экспорт в различные форматы (CSV, PDF)
- [ ] Интеграция с другими API (СПАРК, Контур)
- [ ] Dashboard с real-time обновлениями (WebSockets)
- [ ] Мобильная версия интерфейса
- [ ] Продвинутая аналитика (ML предсказания)
- [ ] Геолокация на картах (Яндекс.Карты, Google Maps)

### Технические улучшения

- [ ] Unit и integration тесты (pytest)
- [ ] CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Контейнеризация приложения (Docker)
- [ ] Kubernetes deployment
- [ ] Мониторинг (Prometheus, Grafana)
- [ ] Tracing (Jaeger, OpenTelemetry)
- [ ] Documentation (Sphinx)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Следуйте PEP 8
- Используйте Black для форматирования (line-length=79)
- Добавляйте docstrings к функциям и классам
- Пишите понятные commit messages

---

## 📄 Лицензия

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Авторы

- **Команда разработки MosProm**

---

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) - за отличный веб-фреймворк
- [SQLAlchemy](https://www.sqlalchemy.org/) - за мощный ORM
- [PostgreSQL](https://www.postgresql.org/) - за надежную БД
- [api-fns.ru](https://api-fns.ru/) - за API доступа к данным ФНС

---

## 📞 Поддержка

Если у вас есть вопросы или предложения:

- 📧 Email: support@mosprom.example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/mosprom/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/mosprom/discussions)

---

**Made with ❤️ in Moscow**
