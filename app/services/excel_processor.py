"""
Excel file processor for organization data.

Обработчик Excel файлов с улучшенной системой ошибок:
- Показывает номер строки с ошибкой
- Показывает название и ИНН предприятия
- Даёт понятное описание проблемы на русском
- Указывает конкретную колонку с ошибкой
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import openpyxl
from sqlalchemy.orm import Session
from app.db.models import Organization, OrganizationMetrics, OrganizationTaxes, OrganizationAssets, OrganizationProducts, OrganizationMeta
from app.logger import get_logger

logger = get_logger(__name__)


def parse_float(value: Any, column_name: str = None) -> Optional[float]:
    """Safely parse float value."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        if column_name:
            raise ValueError(f"Столбец '{column_name}': не удалось преобразовать значение '{value}' в число")
        return None


def parse_int(value: Any, column_name: str = None) -> Optional[int]:
    """Safely parse integer value."""
    if value is None or value == '':
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        if column_name:
            raise ValueError(f"Столбец '{column_name}': не удалось преобразовать значение '{value}' в целое число")
        return None


def parse_bool(value: Any) -> bool:
    """Safely parse boolean value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('да', 'yes', 'true', '1', '+')
    return False


def parse_date(value: Any) -> Optional[datetime]:
    """Safely parse date value."""
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value), '%Y-%m-%d')
    except:
        return None


def process_excel_file(file_path: Path, db: Session) -> Dict[str, Any]:
    """
    Process Excel file and save data to database.
    
    Args:
        file_path: Path to Excel file
        db: Database session
        
    Returns:
        Dict with processing statistics
    """
    logger.info("Starting Excel processing", file=str(file_path))
    
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    
    # Get headers from first row
    headers = []
    for cell in sheet[1]:
        headers.append(cell.value)
    
    organizations_new = 0
    organizations_updated = 0
    rows_processed = 0
    rows_skipped = 0
    errors = []
    
    # Statistics for missing data
    missing_fields = {
        'contacts': 0,
        'coordinates': 0,
        'metrics': 0,
        'taxes': 0,
        'assets': 0,
        'products': 0,
    }
    
    # Detailed organization statistics
    organizations_details = []
    
    # Process each row (skip header)
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        try:
            # Create dict from row data
            data = dict(zip(headers, row))
            
            # Skip empty rows
            if not data.get('ИНН'):
                rows_skipped += 1
                continue
                
            inn = str(data.get('ИНН', '')).strip()
            if not inn:
                rows_skipped += 1
                continue
            
            # Check if organization already exists
            existing_org = db.query(Organization).filter(Organization.inn == inn).first()
            
            if existing_org:
                org = existing_org
                organizations_updated += 1
                logger.info("Organization already exists", inn=inn)
            else:
                # Create new organization
                org = Organization(
                    inn=inn,
                    name=data.get('Наименование организации', '')[:500],
                    full_name=data.get('Полное наименование организации'),
                    status_spark=data.get('Статус СПАРК'),
                    status_internal=data.get('Статус внутренний'),
                    status_final=data.get('Статус ИТОГ'),
                    date_added=parse_date(data.get('Дата добавления в реестр')),
                    legal_address=data.get('Юридический адрес'),
                    production_address=data.get('Адрес производства'),
                    additional_address=data.get('Адрес дополнительной площадки'),
                    main_industry=data.get('Основная отрасль'),
                    main_subindustry=data.get('Подотрасль (Основная)'),
                    extra_industry=data.get('Дополнительная отрасль'),
                    extra_subindustry=data.get('Подотрасль (Дополнительная)'),
                    main_okved=data.get('Основной ОКВЭД (СПАРК)'),
                    main_okved_name=data.get('Вид деятельности по основному ОКВЭД (СПАРК)'),
                    prod_okved=data.get('Производственный ОКВЭД'),
                    prod_okved_name=data.get('Вид деятельности по производственному ОКВЭД'),
                    company_info=data.get('Общие сведения об организации'),
                    company_size=data.get('Размер предприятия (итог)'),
                    company_size_2022=data.get('Размер предприятия (итог) 2022'),
                    size_by_employees=data.get('Размер предприятия (по численности)'),
                    size_by_employees_2022=data.get('Размер предприятия (по численности) 2022'),
                    size_by_revenue=data.get('Размер предприятия (по выручке)'),
                    size_by_revenue_2022=data.get('Размер предприятия (по выручке) 2022'),
                    registration_date=parse_date(data.get('Дата регистрации')),
                    head_name=data.get('Руководитель'),
                    parent_org_name=data.get('Головная организация'),
                    parent_org_inn=data.get('ИНН головной организации'),
                    parent_relation_type=data.get('Вид отношения головной организации'),
                    head_contacts=data.get('Контактные данные руководства'),
                    head_email=data.get('Почта руководства'),
                    employee_contact=data.get('Контакт сотрудника организации'),
                    phone=data.get('Номер телефона'),
                    emergency_contact=data.get('Контактные данные ответственного по ЧС'),
                    website=data.get('Сайт'),
                    email=data.get('Электронная почта'),
                    support_data=data.get('Данные о мерах поддержки'),
                    special_status=data.get('Наличие особого статуса'),
                    site_final=data.get('Площадка итог'),
                    got_moscow_support=parse_bool(data.get('Получена поддержка от г. Москвы')),
                    is_system_critical=parse_bool(data.get('Системообразующее предприятие')),
                    msp_status=data.get('Статус МСП'),
                    coordinates_lat=parse_float(data.get('Координаты (широта)'), 'Координаты (широта)'),
                    coordinates_lon=parse_float(data.get('Координаты (долгота)'), 'Координаты (долгота)'),
                    legal_address_coords=data.get('Координаты юридического адреса'),
                    production_address_coords=data.get('Координаты адреса производства'),
                    additional_address_coords=data.get('Координаты адреса дополнительной площадки'),
                    district=data.get('Округ'),
                    region=data.get('Район'),
                )
                db.add(org)
                db.flush()  # Get org.id
                organizations_new += 1
            
            # Count empty/missing fields for this organization
            empty_fields_count = 0
            empty_fields_list = []
            total_fields = len(data)
            
            for key, value in data.items():
                if value is None or (isinstance(value, str) and value.strip() == ''):
                    empty_fields_count += 1
                    empty_fields_list.append(key)
            
            # Track missing data categories
            has_contacts = any([data.get('Номер телефона'), data.get('Электронная почта'), data.get('Сайт')])
            has_coordinates = any([data.get('Координаты (широта)'), data.get('Координаты (долгота)')])
            
            if not has_contacts:
                missing_fields['contacts'] += 1
            if not has_coordinates:
                missing_fields['coordinates'] += 1
            
            # Add metrics for each year (2017-2023)
            has_metrics = False
            for year in range(2017, 2024):
                try:
                    # Parse revenue with column name tracking
                    revenue_col = f'Выручка предприятия, тыс. руб. {year}'
                    revenue_val = data.get(revenue_col)
                    revenue = None
                    if revenue_val not in (None, ''):
                        try:
                            revenue = float(revenue_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{revenue_col}': не удалось преобразовать значение '{revenue_val}' в число")
                    
                    # Parse profit
                    profit_col = f'Чистая прибыль (убыток),тыс. руб. {year}'
                    profit_val = data.get(profit_col)
                    profit = None
                    if profit_val not in (None, ''):
                        try:
                            profit = float(profit_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{profit_col}': не удалось преобразовать значение '{profit_val}' в число")
                    
                    # Parse total employees
                    total_emp_col = f'Среднесписочная численность персонала (всего по компании), чел {year}'
                    total_emp_val = data.get(total_emp_col)
                    total_employees = None
                    if total_emp_val not in (None, ''):
                        try:
                            temp_val = int(float(total_emp_val)) if total_emp_val else None
                            if temp_val is not None and temp_val > 2147483647:
                                raise ValueError(f"Столбец '{total_emp_col}': значение '{total_emp_val}' слишком велико (максимум: 2,147,483,647)")
                            total_employees = temp_val
                        except (ValueError, TypeError) as e:
                            if "слишком велико" in str(e):
                                raise e
                            raise ValueError(f"Столбец '{total_emp_col}': не удалось преобразовать значение '{total_emp_val}' в целое число")
                    
                    # Parse Moscow employees
                    msk_emp_col = f'Среднесписочная численность персонала, работающего в Москве, чел {year}'
                    msk_emp_val = data.get(msk_emp_col)
                    moscow_employees = None
                    if msk_emp_val not in (None, ''):
                        try:
                            temp_val = int(float(msk_emp_val)) if msk_emp_val else None
                            if temp_val is not None and temp_val > 2147483647:
                                raise ValueError(f"Столбец '{msk_emp_col}': значение '{msk_emp_val}' слишком велико (максимум: 2,147,483,647)")
                            moscow_employees = temp_val
                        except (ValueError, TypeError) as e:
                            if "слишком велико" in str(e):
                                raise e
                            raise ValueError(f"Столбец '{msk_emp_col}': не удалось преобразовать значение '{msk_emp_val}' в целое число")
                    
                    # Parse total FOT
                    total_fot_col = f'Фонд оплаты труда всех сотрудников организации, тыс. руб {year}'
                    total_fot_val = data.get(total_fot_col)
                    total_fot = None
                    if total_fot_val not in (None, ''):
                        try:
                            total_fot = float(total_fot_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{total_fot_col}': не удалось преобразовать значение '{total_fot_val}' в число")
                    
                    # Parse Moscow FOT (multiple possible column names)
                    moscow_fot = None
                    for msk_fot_col in [
                        f'Фонд оплаты труда сотрудников, работающих в Москве, тыс. руб {year}',
                        f'Фонд оплаты труда сотрудников, работающего в Москве, тыс. руб {year}',
                        f'Фонд оплаты труда сотрудников, работающего в Москве, тыс. руб. {year}'
                    ]:
                        msk_fot_val = data.get(msk_fot_col)
                        if msk_fot_val not in (None, ''):
                            try:
                                moscow_fot = float(msk_fot_val)
                                break
                            except (ValueError, TypeError):
                                raise ValueError(f"Столбец '{msk_fot_col}': не удалось преобразовать значение '{msk_fot_val}' в число")
                    
                    # Parse average salary total
                    avg_sal_col = f'Средняя з.п. всех сотрудников организации, тыс.руб. {year}'
                    avg_sal_val = data.get(avg_sal_col)
                    avg_salary_total = None
                    if avg_sal_val not in (None, ''):
                        try:
                            avg_salary_total = float(avg_sal_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{avg_sal_col}': не удалось преобразовать значение '{avg_sal_val}' в число")
                    
                    # Parse average salary Moscow (multiple possible names)
                    avg_salary_moscow = None
                    for avg_msk_col in [
                        f'Средняя з.п. сотрудников, работающих в Москве, тыс.руб. {year}',
                        f'Средняя з.п. сотрудников, работающих в Москве, тыс.руb. {year}'
                    ]:
                        avg_msk_val = data.get(avg_msk_col)
                        if avg_msk_val not in (None, ''):
                            try:
                                avg_salary_moscow = float(avg_msk_val)
                                break
                            except (ValueError, TypeError):
                                raise ValueError(f"Столбец '{avg_msk_col}': не удалось преобразовать значение '{avg_msk_val}' в число")
                    
                    metrics = OrganizationMetrics(
                        organization_id=org.id,
                        year=year,
                        revenue=revenue,
                        profit=profit,
                        total_employees=total_employees,
                        moscow_employees=moscow_employees,
                        total_fot=total_fot,
                        moscow_fot=moscow_fot,
                        avg_salary_total=avg_salary_total,
                        avg_salary_moscow=avg_salary_moscow,
                    )
                    
                    # Add investments (2021-2023)
                    if year >= 2021:
                        inv_col = f'Инвестиции в Мск {year} тыс. руб.'
                        inv_val = data.get(inv_col)
                        if inv_val not in (None, ''):
                            try:
                                metrics.investments = float(inv_val)
                            except (ValueError, TypeError):
                                raise ValueError(f"Столбец '{inv_col}': не удалось преобразовать значение '{inv_val}' в число")
                    
                    # Add export (2019-2023)
                    if year >= 2019:
                        exp_col = f'Объем экспорта, тыс. руб. {year}'
                        exp_val = data.get(exp_col)
                        if exp_val not in (None, ''):
                            try:
                                metrics.export_volume = float(exp_val)
                            except (ValueError, TypeError):
                                raise ValueError(f"Столбец '{exp_col}': не удалось преобразовать значение '{exp_val}' в число")
                        
                    # Only add if there's some data
                    if any([metrics.revenue, metrics.profit, metrics.total_employees]):
                        db.add(metrics)
                        has_metrics = True
                except ValueError as ve:
                    # Re-raise ValueError to be caught by outer exception handler
                    raise ve
            
            if not has_metrics:
                missing_fields['metrics'] += 1
            
            # Add tax data for each year (2017-2024)
            has_taxes = False
            for year in range(2017, 2025):
                try:
                    # Parse total taxes Moscow
                    total_tax_col = f'Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб. {year}'
                    total_tax_val = data.get(total_tax_col)
                    total_taxes_moscow = None
                    if total_tax_val not in (None, ''):
                        try:
                            total_taxes_moscow = float(total_tax_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{total_tax_col}': не удалось преобразовать значение '{total_tax_val}' в число")
                    
                    # Parse profit tax
                    profit_tax_col = f'Налог на прибыль, тыс.руб. {year}'
                    profit_tax_val = data.get(profit_tax_col)
                    profit_tax = None
                    if profit_tax_val not in (None, ''):
                        try:
                            profit_tax = float(profit_tax_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{profit_tax_col}': не удалось преобразовать значение '{profit_tax_val}' в число")
                    
                    # Parse property tax
                    property_tax_col = f'Налог на имущество, тыс.руб. {year}'
                    property_tax_val = data.get(property_tax_col)
                    property_tax = None
                    if property_tax_val not in (None, ''):
                        try:
                            property_tax = float(property_tax_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{property_tax_col}': не удалось преобразовать значение '{property_tax_val}' в число")
                    
                    # Parse land tax (multiple possible names)
                    land_tax = None
                    for land_tax_col in [
                        f'Налог на землю, тыс.руб. {year}',
                        f'Налог на землю, тыс.руb. {year}'
                    ]:
                        land_tax_val = data.get(land_tax_col)
                        if land_tax_val not in (None, ''):
                            try:
                                land_tax = float(land_tax_val)
                                break
                            except (ValueError, TypeError):
                                raise ValueError(f"Столбец '{land_tax_col}': не удалось преобразовать значение '{land_tax_val}' в число")
                    
                    # Parse NDFL
                    ndfl_col = f'НДФЛ, тыс.руб. {year}'
                    ndfl_val = data.get(ndfl_col)
                    ndfl = None
                    if ndfl_val not in (None, ''):
                        try:
                            ndfl = float(ndfl_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{ndfl_col}': не удалось преобразовать значение '{ndfl_val}' в число")
                    
                    # Parse transport tax
                    transport_tax_col = f'Транспортный налог, тыс.руб. {year}'
                    transport_tax_val = data.get(transport_tax_col)
                    transport_tax = None
                    if transport_tax_val not in (None, ''):
                        try:
                            transport_tax = float(transport_tax_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{transport_tax_col}': не удалось преобразовать значение '{transport_tax_val}' в число")
                    
                    # Parse other taxes
                    other_taxes_col = f'Прочие налоги {year}'
                    other_taxes_val = data.get(other_taxes_col)
                    other_taxes = None
                    if other_taxes_val not in (None, ''):
                        try:
                            other_taxes = float(other_taxes_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{other_taxes_col}': не удалось преобразовать значение '{other_taxes_val}' в число")
                    
                    # Parse excise
                    excise_col = f'Акцизы, тыс. руб. {year}'
                    excise_val = data.get(excise_col)
                    excise = None
                    if excise_val not in (None, ''):
                        try:
                            excise = float(excise_val)
                        except (ValueError, TypeError):
                            raise ValueError(f"Столбец '{excise_col}': не удалось преобразовать значение '{excise_val}' в число")
                    
                    taxes = OrganizationTaxes(
                        organization_id=org.id,
                        year=year,
                        total_taxes_moscow=total_taxes_moscow,
                        profit_tax=profit_tax,
                        property_tax=property_tax,
                        land_tax=land_tax,
                        ndfl=ndfl,
                        transport_tax=transport_tax,
                        other_taxes=other_taxes,
                        excise=excise,
                    )
                    if any([taxes.total_taxes_moscow, taxes.profit_tax, taxes.property_tax]):
                        db.add(taxes)
                        has_taxes = True
                except ValueError as ve:
                    # Re-raise ValueError to be caught by outer exception handler
                    raise ve
            
            if not has_taxes:
                missing_fields['taxes'] += 1
            
            # Add assets data
            assets = OrganizationAssets(
                organization_id=org.id,
                cadastral_number_land=data.get('Кадастровый номер ЗУ'),
                land_area=parse_float(data.get('Площадь ЗУ'), 'Площадь ЗУ'),
                land_usage=data.get('Вид разрешенного использования ЗУ'),
                land_ownership_type=data.get('Вид собственности ЗУ'),
                land_owner=data.get('Собственник ЗУ'),
                cadastral_number_building=data.get('Кадастровый номер ОКСа'),
                building_area=parse_float(data.get('Площадь ОКСов'), 'Площадь ОКСов'),
                building_usage=data.get('Вид разрешенного использования ОКСов'),
                building_type=data.get('Тип строения и цель использования'),
                building_purpose=data.get('Назначение ОКСов'),
                building_ownership_type=data.get('Вид собственности ОКСов'),
                building_owner=data.get('СобственникОКСов'),
                production_area=parse_float(data.get('Площадь производственных помещений, кв.м.') or data.get('Площадь производственных помещений'), 'Площадь производственных помещений'),
                property_summary=data.get('Имущественно-земельный комплекс'),
            )
            if any([assets.cadastral_number_land, assets.cadastral_number_building]):
                db.add(assets)
            else:
                missing_fields['assets'] += 1
            
            # Add products data
            products = OrganizationProducts(
                organization_id=org.id,
                product_name=data.get('Производимая продукция'),
                standardized_product=data.get('Стандартизированная продукция') or data.get('Название (виды производимой продукции)'),
                okpd2_codes=data.get('Перечень производимой продукции по кодам ОКПД 2'),
                product_types=data.get('Перечень производимой продукции по типам и сегментам'),
                product_catalog=data.get('Каталог продукции'),
                has_government_orders=parse_bool(data.get('Наличие госзаказа') or data.get('Наличие  госзаказа')),
                capacity_usage=data.get('Уровень загрузки производственных мощностей'),
                has_export=parse_bool(data.get('Наличие поставок продукции на экспорт') or data.get('Наличие поставок продукции на экспорт ')),
                export_volume_last_year=parse_float(data.get('Объем экспорта (млн.руб.) за предыдущий календарный год'), 'Объем экспорта (млн.руб.) за предыдущий календарный год'),
                export_countries=data.get('Перечень государств куда экспортируется продукция') or data.get('Перечень государств куда экспортируется продукция '),
                tnved_code=data.get('Код ТН ВЭД ЕАЭС'),
            )
            if products.product_name:
                db.add(products)
            else:
                missing_fields['products'] += 1
            
            # Add meta data
            meta = OrganizationMeta(
                organization_id=org.id,
                industry_spark=data.get('Отрасль промышленности по Спарк и Справочнику'),
                industry_directory=data.get('Отраслевые презентации'),
                presentation_links=data.get('Ссылки на презентации'),
                registry_development=data.get('Развитие Реестра'),
                other_notes=data.get('Дополнительные примечания'),
            )
            db.add(meta)
            
            # Add organization details to the list
            org_name = data.get('Наименование организации', 'Без названия')[:100]
            organizations_details.append({
                'name': org_name,
                'inn': inn,
                'empty_fields': empty_fields_count,
                'total_fields': total_fields,
                'empty_fields_list': empty_fields_list,
                'missing_contacts': not has_contacts,
                'missing_coordinates': not has_coordinates,
                'is_new': org.id and organizations_new > organizations_updated
            })
            
            rows_processed += 1
            
            # Commit every 100 rows
            if rows_processed % 100 == 0:
                db.commit()
                logger.info("Progress", rows_processed=rows_processed)
                
        except Exception as e:
            error_msg = str(e)
            
            # Преобразуем технические ошибки БД в понятные сообщения
            org_name = data.get('Наименование организации', 'Не указано')
            inn = data.get('ИНН', 'Не указан')
            
            # Определяем тип и описание ошибки с указанием столбца
            column_name = ""
            
            # Check if this is a ValueError from our parsing functions (with column name)
            if isinstance(e, ValueError) and "Столбец" in error_msg:
                error_type = "ОШИБКА ТИПА ДАННЫХ"
                error_desc = error_msg  # Use the detailed message from our parse functions
            
            elif 'integer out of range' in error_msg.lower() or 'numeric value out of range' in error_msg.lower():
                error_type = "ОШИБКА ТИПА ДАННЫХ"
                # Try to identify which column caused the issue
                if 'total_employees' in error_msg:
                    error_desc = "Среднесписочная численность персонала (всего по компании) - значение слишком велико (максимум: 2,147,483,647). Проверьте корректность данных."
                elif 'moscow_employees' in error_msg:
                    error_desc = "Среднесписочная численность персонала, работающего в Москве - значение слишком велико (максимум: 2,147,483,647). Проверьте корректность данных."
                else:
                    error_desc = "Числовое значение слишком велико для колонки базы данных (максимум для целых чисел: 2,147,483,647). Проверьте корректность данных."
            
            elif 'invalid input syntax for type numeric' in error_msg.lower() or 'invalid input syntax for type integer' in error_msg:
                error_type = "ОШИБКА ТИПА ДАННЫХ"
                if 'industry_spark' in error_msg:
                    column_name = "Отрасль промышленности по Спарк и Справочнику"
                    error_desc = f"Столбец '{column_name}' - ожидается число, получен текст"
                elif 'registry_development' in error_msg:
                    column_name = "Развитие Реестра"
                    error_desc = f"Столбец '{column_name}' - ожидается число, получен текст"
                elif 'export_volume_last_year' in error_msg:
                    column_name = "Объем экспорта (млн.руб.) за предыдущий календарный год"
                    # Extract the invalid value from error message if possible
                    import re
                    match = re.search(r'numeric: "([^"]+)"', error_msg)
                    if match:
                        invalid_value = match.group(1)
                        error_desc = f"Столбец '{column_name}': не удалось преобразовать значение '{invalid_value}' в число"
                    else:
                        error_desc = f"Столбец '{column_name}' - ожидается число, получен текст"
                else:
                    error_desc = "В числовой столбец попало текстовое значение"
            
            elif 'foreign key constraint' in error_msg.lower():
                error_type = "ОШИБКА СВЯЗИ"
                error_desc = "Отсутствует связанная запись в базе данных"
            
            elif 'unique constraint' in error_msg.lower() or 'duplicate key' in error_msg.lower():
                if 'inn' in error_msg.lower():
                    error_type = "ДУБЛИКАТ"
                    column_name = "ИНН"
                    error_desc = f"Столбец '{column_name}' - ИНН {inn} уже существует в базе данных"
                else:
                    error_type = "ДУБЛИКАТ"
                    error_desc = "Попытка добавить дублирующуюся запись"
            
            elif 'not-null constraint' in error_msg.lower():
                error_type = "ОТСУТСТВУЕТ ОБЯЗАТЕЛЬНОЕ ПОЛЕ"
                if 'inn' in error_msg.lower():
                    column_name = "ИНН"
                    error_desc = f"Столбец '{column_name}' - не заполнено"
                elif 'name' in error_msg.lower() or 'наименование' in error_msg.lower():
                    column_name = "Наименование организации"
                    error_desc = f"Столбец '{column_name}' - не заполнено"
                else:
                    error_desc = "Не заполнено обязательное поле"
            
            else:
                error_type = "ОШИБКА"
                error_desc = error_msg[:150]
            
            # Формат: ТИП_ОШИБКИ | Название (ИНН: Y) | Строка Excel: X | Описание
            readable_error = f"{error_type} | {org_name} (ИНН: {inn}) | Строка Excel: {row_idx} | {error_desc}"
            
            logger.error("Error processing row", row=row_idx, org_name=org_name, inn=inn, error=error_msg)
            errors.append(readable_error)
            rows_skipped += 1
            continue
    
    # Final commit
    db.commit()
    
    total_organizations = organizations_new + organizations_updated
    
    logger.info("Excel processing completed", 
                organizations_new=organizations_new,
                organizations_updated=organizations_updated,
                rows=rows_processed,
                errors=len(errors))
    
    return {
        "organizations_count": total_organizations,
        "organizations_new": organizations_new,
        "organizations_updated": organizations_updated,
        "rows_processed": rows_processed,
        "rows_skipped": rows_skipped,
        "errors": len(errors),
        "error_details": errors[:10],  # First 10 errors
        "missing_fields": missing_fields,
        "organizations_details": organizations_details[:50],  # First 50 organizations
    }
