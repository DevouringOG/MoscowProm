"""
FNS API Service - fetch organization data from api-fns.ru
"""
import httpx
from typing import Optional, Dict, Any
from app.logger import get_logger

logger = get_logger(__name__)


class FNSAPIService:
    """Service for interacting with FNS API (api-fns.ru)"""
    
    BASE_URL = "https://api-fns.ru/api"
    
    def __init__(self, api_key: str, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_organization_by_inn(self, inn: str) -> Optional[Dict[str, Any]]:
        """
        Fetch organization data from FNS by INN.
        
        Args:
            inn: Organization INN (10 or 12 digits)
            
        Returns:
            Normalized organization data dict or None if not found
        """
        try:
            logger.info("fns_api_request", inn=inn)
            
            # Make request to FNS API
            url = f"{self.BASE_URL}/egr"
            params = {
                "req": inn,
                "key": self.api_key
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if data exists
            if not data or 'items' not in data or not data['items']:
                logger.warning("fns_api_no_data", inn=inn)
                return None
            
            # Get first item (should be the organization)
            org_data = data['items'][0]
            
            # Normalize the data
            normalized = self._normalize_fns_data(org_data)
            
            logger.info("fns_api_success", inn=inn, org_name=normalized.get('name'))
            return normalized
            
        except httpx.HTTPStatusError as e:
            logger.error("fns_api_http_error", inn=inn, status=e.response.status_code, error=str(e))
            return None
        except Exception as e:
            logger.error("fns_api_error", inn=inn, error=str(e))
            return None
    
    def _normalize_fns_data(self, fns_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize FNS API response to application format.
        
        Args:
            fns_data: Raw data from FNS API
            
        Returns:
            Normalized dict with standard fields
        """
        # Determine organization type
        org_type = "ЮЛ"  # Legal entity by default
        if fns_data.get('ЮЛ'):
            org_type = "ЮЛ"
            data = fns_data['ЮЛ']
        elif fns_data.get('ИП'):
            org_type = "ИП"
            data = fns_data['ИП']
        elif fns_data.get('НР'):
            org_type = "НР"
            data = fns_data['НР']
        else:
            data = fns_data
        
        # Extract basic info
        normalized = {
            "inn": data.get('ИНН', ''),
            "ogrn": data.get('ОГРН', '') or data.get('ОГРНИП', ''),
            "kpp": data.get('КПП', ''),
            "org_type": org_type,
            "_raw_data": fns_data
        }
        
        # Name fields
        if org_type == "ИП":
            # For individual entrepreneurs
            fio = data.get('ФИО', {})
            full_name = f"{fio.get('Фамилия', '')} {fio.get('Имя', '')} {fio.get('Отчество', '')}".strip()
            normalized['name'] = full_name
            normalized['full_name'] = f"ИП {full_name}"
            normalized['head_name'] = full_name
        else:
            # For legal entities
            normalized['name'] = data.get('НаимСокрЮЛ', '') or data.get('НаимПолнЮЛ', '')
            normalized['full_name'] = data.get('НаимПолнЮЛ', '') or data.get('НаимСокрЮЛ', '')
            
            # Director/head
            head = data.get('Руководитель', {})
            if isinstance(head, dict):
                head_fio = head.get('ФИО', {})
                if isinstance(head_fio, dict):
                    normalized['head_name'] = f"{head_fio.get('Фамилия', '')} {head_fio.get('Имя', '')} {head_fio.get('Отчество', '')}".strip()
        
        # Address
        address = data.get('Адрес', {})
        if isinstance(address, dict):
            addr_parts = []
            for key in ['Индекс', 'Регион', 'Город', 'Улица', 'Дом', 'Корпус', 'Квартира']:
                if address.get(key):
                    addr_parts.append(str(address[key]))
            normalized['legal_address'] = ', '.join(addr_parts)
        
        # Status
        status = data.get('Статус', '')
        normalized['status'] = status if status else 'Действующее'
        
        # OKVED
        okved = data.get('ОснВидДеят', {})
        if isinstance(okved, dict):
            normalized['main_okved'] = okved.get('Код', '')
            normalized['main_okved_name'] = okved.get('Наим', '')
        
        # Registration date
        reg_date = data.get('ДатаРег', '') or data.get('ДатаОГРН', '')
        normalized['registration_date'] = reg_date
        
        return normalized
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global service instance
_fns_service: Optional[FNSAPIService] = None


def get_fns_service(api_key: str, timeout: int = 30) -> FNSAPIService:
    """
    Get or create FNS API service instance.
    
    Args:
        api_key: FNS API key
        timeout: Request timeout in seconds
        
    Returns:
        FNSAPIService instance
    """
    global _fns_service
    
    if _fns_service is None:
        _fns_service = FNSAPIService(api_key=api_key, timeout=timeout)
    
    return _fns_service
