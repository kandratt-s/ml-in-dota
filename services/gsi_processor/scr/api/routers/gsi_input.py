from fastapi import APIRouter, Depends, Response

from scr.services.process import GSIProcessorService
from scr.schemas.dota_output import GameStateRequest
from scr.api.dependencies import get_GSI_service
from scr.schemas.dota_input import GSIRequest

router = APIRouter(prefix="/gsi-input", tags=["gsi-input"])

@router.post("")
async def process_gsi_data(data: GSIRequest, service: GSIProcessorService = Depends(get_GSI_service)) -> GameStateRequest:
    # await service.process_gsi_data(data)
    # return Response(status_code=200)
    return await service.process_gsi_data(data)