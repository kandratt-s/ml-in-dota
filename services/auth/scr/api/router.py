from fastapi import APIRouter
from scr.api.v1.health import router as health_router
from scr.api.v1.auth import router as register_router


router = APIRouter(prefix="/api/v1")
router.include_router(health_router)
router.include_router(register_router)