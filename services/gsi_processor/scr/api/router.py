from fastapi import APIRouter

from scr.api.routers.gsi_input import router as gsi_input
from scr.api.routers.health import router as health

router = APIRouter()
router.include_router(gsi_input)
router.include_router(health)