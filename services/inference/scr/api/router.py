from fastapi import APIRouter, Request, status

from scr.schemas.inference_response import HealthResponse, ProcessBatchResponse

router = APIRouter(prefix="/inference", tags=["inference"])


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    service = request.app.state.worker_service
    return await service.health_check()


@router.post("/run-once", response_model=ProcessBatchResponse, status_code=status.HTTP_200_OK)
async def run_once(request: Request) -> ProcessBatchResponse:
    service = request.app.state.worker_service
    return await service.process_once()