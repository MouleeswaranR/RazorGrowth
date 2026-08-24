from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config.settings import settings
from app.api.router import api_router
from app.events.event_consumer import register_default_event_consumers
from app.database.session import engine, AsyncSessionLocal
from app.database.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables, events, and background services on application startup."""
    register_default_event_consumers()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI Growth Agent with Razorpay Sandbox Integration",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict:
    """Returns API information. Frontend is served separately via Next.js at port 3000."""
    return {
        "app_name": settings.app_name,
        "version": "1.0.0",
        "description": "Autonomous AI Growth Agent with Razorpay Sandbox Integration",
        "api_docs": "/docs",
        "frontend_url": "http://localhost:3000",
        "status": "operational"
    }


@app.get("/health")
async def health_check() -> dict:
    """Returns application health status and current environment details."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/health/detailed")
async def detailed_health_check() -> dict:
    """Comprehensive health check for demo verification."""
    checks = {}
    
    # Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "✅ Connected"
    except Exception as e:
        checks["database"] = f"❌ Error: {str(e)}"
    
    # Razorpay
    try:
        from app.integrations.razorpay_client import get_razorpay_client
        client = get_razorpay_client()
        checks["razorpay"] = "✅ Configured"
    except Exception as e:
        checks["razorpay"] = f"❌ Error: {str(e)}"
    
    # LLM
    llm_configured = bool(settings.openrouter_api_key)
    checks["llm_service"] = "✅ Configured" if llm_configured else "⚠️ No API key"
    
    # Vector Memory
    try:
        from app.services.vector_memory_service import VectorMemoryService
        svc = VectorMemoryService()
        checks["vector_memory"] = "✅ Ready"
    except Exception as e:
        checks["vector_memory"] = f"⚠️ Warning: {str(e)}"
    
    all_healthy = all("✅" in v for v in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
