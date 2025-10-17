"""Excel file processor for organization data."""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import openpyxl
from sqlalchemy.orm import Session
from app.db.models import Organization, OrganizationMetrics, OrganizationTaxes, OrganizationAssets, OrganizationProducts, OrganizationMeta
from app.logger import get_logger

logger = get_logger(__name__)


def parse_float(value: Any) -> Optional[float]:
    """Safely parse float value."""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_int(value: Any) -> Optional[int]:
    """Safely parse integer value."""
    if value is None or value == '':
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
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
    
    organizations_count = 0
    rows_processed = 0
    errors = []
    
    # Process each row (skip header)
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
        try:
            # Create dict from row data
            data = dict(zip(headers, row))
            
            # Skip empty rows
            if not data.get('ИНН'):
                continue
                
            inn = str(data.get('ИНН', '')).strip()
            if not inn:
                continue
            
            # Check if organization already exists
            existing_org = db.query(Organization).filter(Organization.inn == inn).first()
            
            if existing_org:
                org = existing_org
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
                    coordinates_lat=parse_float(data.get('Координаты (широта)')),
                    coordinates_lon=parse_float(data.get('Координаты (долгота)')),
                    legal_address_coords=data.get('Координаты юридического адреса'),
                    production_address_coords=data.get('Координаты адреса производства'),
                    additional_address_coords=data.get('Координаты адреса дополнительной площадки'),
                    district=data.get('Округ'),
                    region=data.get('Район'),
                )
                db.add(org)
                db.flush()  # Get org.id
                organizations_count += 1
            
            # Add metrics for each year (2017-2023)
            for year in range(2017, 2024):
                metrics = OrganizationMetrics(
                    organization_id=org.id,
                    year=year,
                    revenue=parse_float(data.get(f'Выручка предприятия, тыс. руб. {year}')),
                    profit=parse_float(data.get(f'Чистая прибыль (убыток),тыс. руб. {year}')),
                    total_employees=parse_int(data.get(f'Среднесписочная численность персонала (всего по компании), чел {year}')),
                    moscow_employees=parse_int(data.get(f'Среднесписочная численность персонала, работающего в Москве, чел {year}')),
                    total_fot=parse_float(data.get(f'Фонд оплаты труда всех сотрудников организации, тыс. руб {year}')),
                    moscow_fot=parse_float(data.get(f'Фонд оплаты труда сотрудников, работающих в Москве, тыс. руб {year}') or 
                                         parse_float(data.get(f'Фонд оплаты труда сотрудников, работающего в Москве, тыс. руб {year}') or
                                         parse_float(data.get(f'Фонд оплаты труда сотрудников, работающего в Москве, тыс. руб. {year}')))),
                    avg_salary_total=parse_float(data.get(f'Средняя з.п. всех сотрудников организации, тыс.руб. {year}')),
                    avg_salary_moscow=parse_float(data.get(f'Средняя з.п. сотрудников, работающих в Москве, тыс.руб. {year}') or
                                                 parse_float(data.get(f'Средняя з.п. сотрудников, работающих в Москве, тыс.руb. {year}'))),
                )
                # Add investments (2021-2023)
                if year >= 2021:
                    metrics.investments = parse_float(data.get(f'Инвестиции в Мск {year} тыс. руб.'))
                # Add export (2019-2023)
                if year >= 2019:
                    metrics.export_volume = parse_float(data.get(f'Объем экспорта, тыс. руб. {year}'))
                    
                # Only add if there's some data
                if any([metrics.revenue, metrics.profit, metrics.total_employees]):
                    db.add(metrics)
            
            # Add tax data for each year (2017-2024)
            for year in range(2017, 2025):
                taxes = OrganizationTaxes(
                    organization_id=org.id,
                    year=year,
                    total_taxes_moscow=parse_float(data.get(f'Налоги, уплаченные в бюджет Москвы (без акцизов), тыс.руб. {year}')),
                    profit_tax=parse_float(data.get(f'Налог на прибыль, тыс.руб. {year}')),
                    property_tax=parse_float(data.get(f'Налог на имущество, тыс.руб. {year}')),
                    land_tax=parse_float(data.get(f'Налог на землю, тыс.руб. {year}') or
                                        parse_float(data.get(f'Налог на землю, тыс.руb. {year}'))),
                    ndfl=parse_float(data.get(f'НДФЛ, тыс.руб. {year}')),
                    transport_tax=parse_float(data.get(f'Транспортный налог, тыс.руб. {year}')),
                    other_taxes=parse_float(data.get(f'Прочие налоги {year}')),
                    excise=parse_float(data.get(f'Акцизы, тыс. руб. {year}')),
                )
                if any([taxes.total_taxes_moscow, taxes.profit_tax, taxes.property_tax]):
                    db.add(taxes)
            
            # Add assets data
            assets = OrganizationAssets(
                organization_id=org.id,
                cadastral_number_land=data.get('Кадастровый номер ЗУ'),
                land_area=parse_float(data.get('Площадь ЗУ')),
                land_usage=data.get('Вид разрешенного использования ЗУ'),
                land_ownership_type=data.get('Вид собственности ЗУ'),
                land_owner=data.get('Собственник ЗУ'),
                cadastral_number_building=data.get('Кадастровый номер ОКСа'),
                building_area=parse_float(data.get('Площадь ОКСов')),
                building_usage=data.get('Вид разрешенного использования ОКСов'),
                building_type=data.get('Тип строения и цель использования'),
                building_purpose=data.get('Назначение ОКСов'),
                building_ownership_type=data.get('Вид собственности ОКСов'),
                building_owner=data.get('СобственникОКСов'),
                production_area=parse_float(data.get('Площадь производственных помещений, кв.м.') or data.get('Площадь производственных помещений')),
                property_summary=data.get('Имущественно-земельный комплекс'),
            )
            if any([assets.cadastral_number_land, assets.cadastral_number_building]):
                db.add(assets)
            
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
                export_volume_last_year=parse_float(data.get('Объем экспорта (млн.руб.) за предыдущий календарный год')),
                export_countries=data.get('Перечень государств куда экспортируется продукция') or data.get('Перечень государств куда экспортируется продукция '),
                tnved_code=data.get('Код ТН ВЭД ЕАЭС'),
            )
            if products.product_name:
                db.add(products)
            
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
            
            rows_processed += 1
            
            # Commit every 100 rows
            if rows_processed % 100 == 0:
                db.commit()
                logger.info("Progress", rows_processed=rows_processed)
                
        except Exception as e:
            logger.error("Error processing row", row=row_idx, error=str(e))
            errors.append(f"Row {row_idx}: {str(e)}")
            continue
    
    # Final commit
    db.commit()
    
    logger.info("Excel processing completed", 
                organizations=organizations_count, 
                rows=rows_processed,
                errors=len(errors))
    
    return {
        "organizations_count": organizations_count,
        "rows_processed": rows_processed,
        "errors": len(errors),
        "error_details": errors[:10]  # First 10 errors
    }
