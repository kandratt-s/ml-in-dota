

from fastapi import Request

from scr.services.process import GSIProcessorService


def get_GSI_service(request: Request) -> GSIProcessorService:
    return request.app.state.GSI_processor_service
