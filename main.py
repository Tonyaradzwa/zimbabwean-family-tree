from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(
    title="Zimbabwean Family Tree",
    description="Backend for storing Shona kinship-based family trees",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")