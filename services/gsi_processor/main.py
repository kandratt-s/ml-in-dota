from fastapi import FastAPI
from .scr.api.routers import router


app = FastAPI()
app.include_router(router=router)