from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.services.fns_api import get_fns_service
from app.logger import get_logger
from config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/api/fns", tags=["fns"])


@router.get("/organization/{inn}")
async def get_organization_from_fns(inn: str):
    try:
        if not inn or not inn.isdigit() or len(inn) not in [10, 12]:
            raise HTTPException(
                status_code=400,
                detail="Invalid INN format. Must be 10 or 12 digits.",
            )

        fns_enabled = getattr(settings.get("fns_api", {}), "enabled", False)
        if not fns_enabled:
            raise HTTPException(status_code=503, detail="FNS API is disabled")

        fns_config = settings.get("fns_api", {})
        api_key = getattr(fns_config, "api_key", None)
        timeout = getattr(fns_config, "timeout", 30)

        if not api_key:
            raise HTTPException(
                status_code=503, detail="FNS API key not configured"
            )

        fns_service = get_fns_service(api_key=api_key, timeout=timeout)

        logger.info("fetching_fns_data_for_form", inn=inn)
        fns_data = await fns_service.get_organization_by_inn(inn)

        if not fns_data:
            raise HTTPException(
                status_code=404,
                detail="Organization not found in FNS database",
            )

        logger.info(
            "fns_data_fetched_for_form", inn=inn, name=fns_data.get("name")
        )

        return JSONResponse(
            content={
                "status": "success",
                "message": "Organization data fetched from FNS",
                "data": fns_data,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("fns_data_fetch_failed", inn=inn, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch data from FNS: {str(e)}"
        )
