from fastapi import APIRouter

from scr.schemas import GSIDota

router = APIRouter(prefix="/gsi-input", tags=["gsi-input"])

@router.post("")
async def process_gsi_data(data: GSIDota):
    pass