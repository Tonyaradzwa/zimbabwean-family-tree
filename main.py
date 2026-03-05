from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.api import router as api_router

app = FastAPI(
    title="Zimbabwean Family Tree",
    description="Backend for storing Shona kinship-based family trees",
    version="1.0.0"
)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(api_router, prefix="/api/v1")