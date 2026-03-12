from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api import router as api_router
from app.db import engine
from app.models.family import Base

app = FastAPI(
    title="Zimbabwean Family Tree",
    description="Backend for storing Shona kinship-based family trees",
    version="1.0.0"
)


@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(api_router, prefix="/api/v1")