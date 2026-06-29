from fastapi import APIRouter, Depends
from app.core.auth import get_api_key
from app.services.dashboard_service import DashboardServiceAPI

router = APIRouter(prefix="", tags=["dashboard"], dependencies=[Depends(get_api_key)])
service = DashboardServiceAPI()

@router.get("/dashboard")
def dashboard():
    return service.get_dashboard()
