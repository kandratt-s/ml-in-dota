from fastapi import APIRouter, Depends

from scr.schemas.dota_output import GameStateRequest
from scr.schemas.dota_input import GSIRequest
from scr.services.process import GSIProcessorService

from scr.api.dependencies import get_GSI_service

router = APIRouter(prefix="/gsi-input", tags=["gsi-input"])

@router.post("", response_model=GameStateRequest)
async def process_gsi_data(
    data: GSIRequest,
    service: GSIProcessorService = Depends(get_GSI_service),
) -> GameStateRequest:
    return await service.process_gsi_data(data)
