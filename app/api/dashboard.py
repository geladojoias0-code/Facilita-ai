from fastapi import APIRouter
from app.services.dashboard_service import DashboardServiceAPI

router = APIRouter(prefix="", tags=["dashboard"])
service = DashboardServiceAPI()

@router.get("/dashboard")
def dashboard():
    return service.get_dashboard()
