from app.services.lead_service import DashboardService

service = DashboardService()

class DashboardServiceAPI:
    def get_dashboard(self):
        return service.stats()
