"""
Excel file processor v2 - использует индексы столбцов вместо названий.

Точные индексы столбцов из Excel файла (0-based):
- 0: №
- 1: ИНН
- 2: Наименование организации
- 47-53: Выручка 2017-2023
- 54-60: Прибыль 2017-2023  
- 61-67: Численность всего 2017-2023
- 68-74: Численность Москва 2017-2023
- 75-81: ФОТ всего 2017-2023
- 82-88: ФОТ Москва 2017-2023
- 89-95: Средняя ЗП всего 2017-2023
- 96-102: Средняя ЗП Москва 2017-2023
- 103-110: Налоги всего 2017-2024
- 111-118: Налог на прибыль 2017-2024
- 119-126: Налог на имущество 2017-2024
- 127-134: Налог на землю 2017-2024
- 135-142: НДФЛ 2017-2024
- 143-150: Транспортный налог 2017-2024
- 151-158: Прочие налоги 2017-2024
- 159-166: Акцизы 2017-2024
- 167-169: Инвестиции 2021-2023
- 170-174: Экспорт 2019-2023
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import openpyxl
from sqlalchemy.orm import Session
from app.db.models import (
    Organization,
    OrganizationMetrics,
    OrganizationTaxes,
    OrganizationAssets,
    OrganizationProducts,
    OrganizationMeta,
)
from app.logger import get_logger

logger = get_logger(__name__)


def safe_str(value, max_len=None):
    """Safely convert value to string."""
    if value is None or value == "":
        return None
    result = str(value).strip()
    if max_len and len(result) > max_len:
        result = result[:max_len]
    return result if result else None


def safe_float(value):
    """Safely convert value to float."""
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value):
    """Safely convert value to int."""
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def safe_bool(value):
    """Safely convert value to boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower().strip() in ("да", "yes", "true", "1", "+")
    return False


def safe_date(value):
    """Safely parse date value."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        # Try different date formats
        date_str = str(value).strip()
        for fmt in ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
    except:
        return None


def process_excel_file(file_path: Path, db: Session) -> Dict[str, Any]:
    """
    Process Excel file using column indices instead of names.

    Args:
        file_path: Path to Excel file
        db: Database session

    Returns:
        Dict with processing statistics
    """
    logger.info(
        "Starting Excel processing v2 (index-based)", file=str(file_path)
    )

    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active

    organizations_new = 0
    organizations_updated = 0
    rows_processed = 0
    rows_skipped = 0
    errors = []
    organizations_details = (
        []
    )  # Список с информацией о загруженных организациях

    # Process each row (skip header)
    for row_idx, row in enumerate(
        sheet.iter_rows(min_row=2, values_only=True), start=2
    ):
        try:
            logger.info(
                f"Processing row {row_idx}: {len(row)} columns, INN={row[1] if len(row) > 1 else 'N/A'}"
            )

            # Get INN from column 1
            inn = safe_str(row[1])
            if not inn:
                rows_skipped += 1
                continue

            # Check if organization already exists
            existing_org = (
                db.query(Organization).filter(Organization.inn == inn).first()
            )

            is_new = False
            if existing_org:
                org = existing_org
                organizations_updated += 1
                logger.info(
                    f"Updating organization", inn=inn, name=safe_str(row[2])
                )

                # Delete existing metrics and taxes to update with fresh data
                db.query(OrganizationMetrics).filter(
                    OrganizationMetrics.organization_id == org.id
                ).delete()
                db.query(OrganizationTaxes).filter(
                    OrganizationTaxes.organization_id == org.id
                ).delete()

            else:
                is_new = True
                # Create new organization
                org = Organization(
                    inn=inn,
                    name=safe_str(row[2], 500),  # Наименование организации
                    full_name=safe_str(row[3]),  # Полное наименование
                    status_spark=safe_str(row[4]),  # Статус СПАРК
                    status_internal=safe_str(row[5]),  # Статус внутренний
                    status_final=safe_str(row[6]),  # Статус ИТОГ
                    date_added=safe_date(row[7]),  # Дата добавления в реестр
                    legal_address=safe_str(row[8]),  # Юридический адрес
                    production_address=safe_str(row[9]),  # Адрес производства
                    additional_address=safe_str(
                        row[10]
                    ),  # Адрес дополнительной площадки
                    main_industry=safe_str(row[11]),  # Основная отрасль
                    main_subindustry=safe_str(
                        row[12]
                    ),  # Подотрасль (Основная)
                    extra_industry=safe_str(row[13]),  # Дополнительная отрасль
                    extra_subindustry=safe_str(
                        row[14]
                    ),  # Подотрасль (Дополнительная)
                    main_okved=safe_str(row[16]),  # Основной ОКВЭД (СПАРК)
                    main_okved_name=safe_str(
                        row[17]
                    ),  # Вид деятельности по основному ОКВЭД
                    prod_okved=safe_str(row[18]),  # Производственный ОКВЭД
                    prod_okved_name=safe_str(
                        row[19]
                    ),  # Вид деятельности по производственному ОКВЭД
                    company_info=safe_str(row[20]),  # Общие сведения
                    company_size=safe_str(
                        row[21]
                    ),  # Размер предприятия (итог)
                    company_size_2022=safe_str(
                        row[22]
                    ),  # Размер предприятия (итог) 2022
                    size_by_employees=safe_str(
                        row[23]
                    ),  # Размер предприятия (по численности)
                    size_by_employees_2022=safe_str(
                        row[24]
                    ),  # Размер предприятия (по численности) 2022
                    size_by_revenue=safe_str(
                        row[25]
                    ),  # Размер предприятия (по выручке)
                    size_by_revenue_2022=safe_str(
                        row[26]
                    ),  # Размер предприятия (по выручке) 2022
                    registration_date=safe_date(row[27]),  # Дата регистрации
                    head_name=safe_str(row[28]),  # Руководитель
                    parent_org_name=safe_str(row[29]),  # Головная организация
                    parent_org_inn=safe_str(
                        row[30]
                    ),  # ИНН головной организации
                    parent_relation_type=safe_str(
                        row[31]
                    ),  # Вид отношения головной организации
                    head_contacts=safe_str(
                        row[32]
                    ),  # Контактные данные руководства
                    head_email=safe_str(row[33]),  # Почта руководства
                    employee_contact=safe_str(
                        row[34]
                    ),  # Контакт сотрудника организации
                    phone=safe_str(row[35]),  # Номер телефона
                    emergency_contact=safe_str(
                        row[36]
                    ),  # Контактные данные ответственного по ЧС
                    website=safe_str(row[37]),  # Сайт
                    email=safe_str(row[38]),  # Электронная почта
                    support_data=safe_str(row[39]),  # Данные о мерах поддержки
                    special_status=safe_str(
                        row[40]
                    ),  # Наличие особого статуса
                    site_final=safe_str(row[41]),  # Площадка итог
                    got_moscow_support=safe_bool(
                        row[42]
                    ),  # Получена поддержка от г. Москвы
                    is_system_critical=safe_bool(
                        row[43]
                    ),  # Системообразующее предприятие
                    msp_status=safe_str(row[44]),  # Статус МСП
                    coordinates_lat=safe_float(
                        row[205] if len(row) > 205 else None
                    ),  # Координаты (широта)
                    coordinates_lon=safe_float(
                        row[206] if len(row) > 206 else None
                    ),  # Координаты (долгота)
                    legal_address_coords=safe_str(
                        row[202] if len(row) > 202 else None
                    ),  # Координаты юр. адреса
                    production_address_coords=safe_str(
                        row[203] if len(row) > 203 else None
                    ),  # Координаты адреса производства
                    additional_address_coords=safe_str(
                        row[204] if len(row) > 204 else None
                    ),  # Координаты доп. площадки
                    district=safe_str(
                        row[207] if len(row) > 207 else None
                    ),  # Округ
                    region=safe_str(
                        row[208] if len(row) > 208 else None
                    ),  # Район
                )
                db.add(org)
                db.flush()  # Get org.id
                organizations_new += 1
                logger.info(
                    f"Created new organization", inn=inn, name=org.name
                )

            # Add metrics for years 2017-2023
            for year_idx, year in enumerate(range(2017, 2024)):
                # Column indices:
                # Revenue: 47-53 (2017-2023)
                # Profit: 54-60
                # Total employees: 61-67
                # Moscow employees: 68-74
                # Total FOT: 75-81
                # Moscow FOT: 82-88
                # Avg salary total: 89-95
                # Avg salary Moscow: 96-102

                revenue = safe_float(row[47 + year_idx])
                profit = safe_float(row[54 + year_idx])
                total_employees = safe_int(row[61 + year_idx])
                moscow_employees = safe_int(row[68 + year_idx])
                total_fot = safe_float(row[75 + year_idx])
                moscow_fot = safe_float(row[82 + year_idx])
                avg_salary_total = safe_float(row[89 + year_idx])
                avg_salary_moscow = safe_float(row[96 + year_idx])

                # Investment data only for 2021-2023 (indices 167-169)
                investments = None
                if year == 2021:
                    investments = safe_float(
                        row[167] if len(row) > 167 else None
                    )
                elif year == 2022:
                    investments = safe_float(
                        row[168] if len(row) > 168 else None
                    )
                elif year == 2023:
                    investments = safe_float(
                        row[169] if len(row) > 169 else None
                    )

                # Export data only for 2019-2023 (indices 170-174)
                export_volume = None
                if year == 2019:
                    export_volume = safe_float(
                        row[170] if len(row) > 170 else None
                    )
                elif year == 2020:
                    export_volume = safe_float(
                        row[171] if len(row) > 171 else None
                    )
                elif year == 2021:
                    export_volume = safe_float(
                        row[172] if len(row) > 172 else None
                    )
                elif year == 2022:
                    export_volume = safe_float(
                        row[173] if len(row) > 173 else None
                    )
                elif year == 2023:
                    export_volume = safe_float(
                        row[174] if len(row) > 174 else None
                    )

                # Only create metrics if we have at least one value
                if any(
                    [
                        revenue,
                        profit,
                        total_employees,
                        moscow_employees,
                        total_fot,
                        moscow_fot,
                        avg_salary_total,
                        avg_salary_moscow,
                        investments,
                        export_volume,
                    ]
                ):

                    metric = OrganizationMetrics(
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
                        investments=investments,
                        export_volume=export_volume,
                    )
                    db.add(metric)

            # Add taxes for years 2017-2024
            for year_idx, year in enumerate(range(2017, 2025)):
                # Tax column indices:
                # Total taxes: 103-110 (2017-2024)
                # Profit tax: 111-118
                # Property tax: 119-126
                # Land tax: 127-134
                # NDFL: 135-142
                # Transport tax: 143-150
                # Other taxes: 151-158
                # Excise: 159-166

                total_taxes_moscow = safe_float(row[103 + year_idx])
                profit_tax = safe_float(row[111 + year_idx])
                property_tax = safe_float(row[119 + year_idx])
                land_tax = safe_float(row[127 + year_idx])
                ndfl = safe_float(row[135 + year_idx])
                transport_tax = safe_float(row[143 + year_idx])
                other_taxes = safe_float(row[151 + year_idx])
                excise = safe_float(row[159 + year_idx])

                # Only create tax record if we have at least one value
                if any(
                    [
                        total_taxes_moscow,
                        profit_tax,
                        property_tax,
                        land_tax,
                        ndfl,
                        transport_tax,
                        other_taxes,
                        excise,
                    ]
                ):

                    tax = OrganizationTaxes(
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
                    db.add(tax)

            # Add assets (if we have asset data)
            if len(row) > 175:
                # Asset column indices (approximate):
                # 175: Имущественно-земельный комплекс
                # 176: Кадастровый номер ЗУ
                # 177: Площадь ЗУ
                # 178: Вид разрешенного использования ЗУ
                # 179: Вид собственности ЗУ
                # 180: Собственник ЗУ
                # 181: Кадастровый номер ОКСа
                # 182: Площадь ОКСов
                # 183: Вид разрешенного использования ОКСов
                # 184: Тип строения и цель использования
                # 185: Вид собственности ОКСов
                # 186: СобственникОКСов
                # 187: Площадь производственных помещений

                has_assets = any(
                    [
                        row[176] if len(row) > 176 else None,
                        row[181] if len(row) > 181 else None,
                    ]
                )

                if has_assets:
                    # Delete existing assets first
                    db.query(OrganizationAssets).filter(
                        OrganizationAssets.organization_id == org.id
                    ).delete()

                    asset = OrganizationAssets(
                        organization_id=org.id,
                        property_summary=safe_str(
                            row[175] if len(row) > 175 else None
                        ),
                        cadastral_number_land=safe_str(
                            row[176] if len(row) > 176 else None
                        ),
                        land_area=safe_float(
                            row[177] if len(row) > 177 else None
                        ),
                        land_usage=safe_str(
                            row[178] if len(row) > 178 else None
                        ),
                        land_ownership_type=safe_str(
                            row[179] if len(row) > 179 else None
                        ),
                        land_owner=safe_str(
                            row[180] if len(row) > 180 else None
                        ),
                        cadastral_number_building=safe_str(
                            row[181] if len(row) > 181 else None
                        ),
                        building_area=safe_float(
                            row[182] if len(row) > 182 else None
                        ),
                        building_usage=safe_str(
                            row[183] if len(row) > 183 else None
                        ),
                        building_type=safe_str(
                            row[184] if len(row) > 184 else None
                        ),
                        building_ownership_type=safe_str(
                            row[185] if len(row) > 185 else None
                        ),
                        building_owner=safe_str(
                            row[186] if len(row) > 186 else None
                        ),
                        production_area=safe_float(
                            row[187] if len(row) > 187 else None
                        ),
                    )
                    db.add(asset)

            # Add products (if we have product data)
            if len(row) > 188:
                has_products = any(
                    [
                        (
                            row[188] if len(row) > 188 else None
                        ),  # Производимая продукция
                        (
                            row[190] if len(row) > 190 else None
                        ),  # Название (виды производимой продукции)
                    ]
                )

                if has_products:
                    # Delete existing products first
                    db.query(OrganizationProducts).filter(
                        OrganizationProducts.organization_id == org.id
                    ).delete()

                    product = OrganizationProducts(
                        organization_id=org.id,
                        product_name=safe_str(
                            row[188] if len(row) > 188 else None
                        ),  # Производимая продукция
                        standardized_product=safe_str(
                            row[189] if len(row) > 189 else None
                        ),  # Стандартизированная продукция
                        product_types=safe_str(
                            row[190] if len(row) > 190 else None
                        ),  # Название (виды)
                        okpd2_codes=safe_str(
                            row[191] if len(row) > 191 else None
                        ),  # Перечень по ОКПД 2
                        product_catalog=safe_str(
                            row[193] if len(row) > 193 else None
                        ),  # Каталог продукции
                        has_government_orders=safe_bool(
                            row[194] if len(row) > 194 else None
                        ),  # Наличие госзаказа
                        capacity_usage=safe_str(
                            row[195] if len(row) > 195 else None
                        ),  # Уровень загрузки
                        has_export=safe_bool(
                            row[196] if len(row) > 196 else None
                        ),  # Наличие экспорта
                        export_volume_last_year=safe_float(
                            row[197] if len(row) > 197 else None
                        ),  # Объем экспорта
                        export_countries=safe_str(
                            row[198] if len(row) > 198 else None
                        ),  # Перечень государств
                        tnved_code=safe_str(
                            row[199] if len(row) > 199 else None
                        ),  # Код ТН ВЭД
                    )
                    db.add(product)

            # Add meta (if we have meta data)
            if len(row) > 200:
                has_meta = any(
                    [
                        (
                            row[200] if len(row) > 200 else None
                        ),  # Развитие Реестра
                        (
                            row[201] if len(row) > 201 else None
                        ),  # Отрасль промышленности
                    ]
                )

                if has_meta:
                    # Delete existing meta first
                    db.query(OrganizationMeta).filter(
                        OrganizationMeta.organization_id == org.id
                    ).delete()

                    meta = OrganizationMeta(
                        organization_id=org.id,
                        registry_development=safe_str(
                            row[200] if len(row) > 200 else None
                        ),
                        industry_spark=safe_str(
                            row[201] if len(row) > 201 else None
                        ),
                    )
                    db.add(meta)

            # Collect information about this organization (only first 50 to avoid huge response)
            if len(organizations_details) < 50:
                organizations_details.append(
                    {
                        "inn": org.inn,
                        "name": org.name or "Без названия",
                        "is_new": is_new,
                        "empty_fields": 0,  # Will be calculated below
                        "empty_fields_list": [],  # List of empty field names
                    }
                )

            rows_processed += 1

            # Commit every 100 rows
            if rows_processed % 100 == 0:
                db.commit()
                logger.info(f"Processed {rows_processed} rows")

        except Exception as e:
            errors.append(
                {
                    "row": row_idx,
                    "inn": safe_str(row[1]) if len(row) > 1 else "Unknown",
                    "name": safe_str(row[2]) if len(row) > 2 else "Unknown",
                    "error": str(e),
                }
            )
            logger.error(f"Error processing row {row_idx}", error=str(e))
            continue

    # Final commit
    db.commit()

    logger.info(
        "Excel processing completed",
        new=organizations_new,
        updated=organizations_updated,
        total=rows_processed,
        skipped=rows_skipped,
        errors=len(errors),
    )

    return {
        "organizations_new": organizations_new,
        "organizations_updated": organizations_updated,
        "organizations_count": organizations_new
        + organizations_updated,  # Total organizations processed
        "rows_processed": rows_processed,
        "rows_skipped": rows_skipped,
        "errors": len(errors),
        "error_details": [err for err in errors[:20]],  # First 20 errors only
        "organizations_details": organizations_details,  # Detailed list of organizations
    }
