from fastapi import APIRouter, Request

from scr.schemas.dota_output import GameStateRequest
from scr.schemas.dota_input import GSIRequest

router = APIRouter(prefix="/gsi-input", tags=["gsi-input"])

@router.post("", response_model=GameStateRequest)
async def process_gsi_data(data: GSIRequest, request: Request) -> GameStateRequest:
    service = request.app.state.GSI_processor_service
    return await service.process_gsi_data(data)

@router.post("/test")
async def test_process(data, request: Request):
    _ = request.app.state.GSI_processor_service
    print(data)
    return None