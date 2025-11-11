# controllers/GuestInfoController.py
from entities.PlatformInfo import PlatformInfo

class GuestInfoController:
    @staticmethod
    def fetch_platform_info():
        info = PlatformInfo.query.first()
        return {
            "csrPurpose": info.csrPurpose if info else "No purpose defined yet.",
            "features": info.features if info else "No features defined yet."
        }

    @staticmethod
    def present_csr_details():
        info = PlatformInfo.query.first()
        return {
            "roles": info.roles if info else "No roles defined yet.",
            "impactStories": info.impactStories if info else "No stories available yet."
        }