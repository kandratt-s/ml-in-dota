from fastapi import APIRouter, Depends

from scr.schemas import GSIRequest
from scr.services.process import GSIProcessorService
from scr.schemas.dota_output import GameStateRequest

router = APIRouter(prefix="/gsi-input", tags=["gsi-input"])

@router.post("")
async def process_gsi_data(data: GSIRequest, service: GSIProcessorService = Depends()) -> GameStateRequest:
    return await service.process_gsi_data(data)