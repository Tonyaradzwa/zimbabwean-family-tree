from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api import router as api_router
from app.db import engine
from app.models.family import Base

app = FastAPI(
    title="Zimbabwean Family Tree",
    description="Backend for storing Shona kinship-based family trees",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    # Allow local dev frontends and Codespaces forwarded frontend URLs.
    allow_origin_regex=r"^((https?://(localhost|127\.0\.0\.1)(:\d+)?)|(https://[a-z0-9-]+\.app\.github\.dev))$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

app.include_router(api_router, prefix="/api/v1")