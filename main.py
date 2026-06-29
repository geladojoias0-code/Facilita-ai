from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.limiter import limiter
from app.core.database import init_db
from app.api import leads, conversas, coach, producao, dashboard
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="FACILITA AI CRM")

app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://facilitaweb.shop", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads.router)
app.include_router(conversas.router)
app.include_router(coach.router)
app.include_router(producao.router)
app.include_router(dashboard.router)


@app.on_event("startup")
async def startup_event():
    init_db(settings.DB_PATH)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
