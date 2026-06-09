from fastapi import APIRouter
from app.api.v1.endpoints import announcements, filters, companies, applications, price, dashboard, auth, chat

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(announcements.router)
router.include_router(filters.router)
router.include_router(companies.router)
router.include_router(applications.router)
router.include_router(price.router)
router.include_router(dashboard.router)
router.include_router(chat.router)
