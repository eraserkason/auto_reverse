from fastapi import APIRouter

from api.auth import router as auth_router
from api.auto_reverse import router as auto_reverse_router
from api.browser_task import router as browser_task_router
from api.dashboard import router as dashboard_router
from api.users import router as users_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(dashboard_router)
api_router.include_router(auto_reverse_router)
api_router.include_router(browser_task_router)
