from fastapi import APIRouter

from api.routers import health, gsi_input

router = APIRouter()
router.include_router(gsi_input.router)
router.include_router(health.router)