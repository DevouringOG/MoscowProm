"""Script to clear all organization data from database."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import get_database_url

# Import models directly
from app.db.models import (
    Organization, 
    OrganizationMetrics, 
    OrganizationTaxes, 
    OrganizationAssets, 
    OrganizationProducts, 
    OrganizationMeta
)

def clear_database():
    """Clear all organization data from database."""
    # Create engine and session
    database_url = get_database_url()
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Delete all data in reverse order (to avoid foreign key issues)
        deleted_meta = db.query(OrganizationMeta).delete()
        deleted_products = db.query(OrganizationProducts).delete()
        deleted_assets = db.query(OrganizationAssets).delete()
        deleted_taxes = db.query(OrganizationTaxes).delete()
        deleted_metrics = db.query(OrganizationMetrics).delete()
        deleted_orgs = db.query(Organization).delete()
        
        db.commit()
        
        print('✅ База данных очищена успешно!\n')
        print('Удалено записей:')
        print(f'  • Организации: {deleted_orgs}')
        print(f'  • Метрики: {deleted_metrics}')
        print(f'  • Налоги: {deleted_taxes}')
        print(f'  • Активы: {deleted_assets}')
        print(f'  • Продукция: {deleted_products}')
        print(f'  • Метаданные: {deleted_meta}')
        print(f'\nВсего удалено: {deleted_orgs + deleted_metrics + deleted_taxes + deleted_assets + deleted_products + deleted_meta} записей')
        
        return True
    except Exception as e:
        db.rollback()
        print(f'❌ Ошибка при очистке БД: {e}')
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    clear_database()
