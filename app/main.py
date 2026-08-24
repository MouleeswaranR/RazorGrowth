from contextlib import asynccontextmanager
from datetime import datetime
import time
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
    await _warm_up_rag()
    yield
    await engine.dispose()


async def _warm_up_rag() -> None:
    """Pre-loads the embedding model and ChromaDB collection at boot.

    Both are lazily constructed on first use, which otherwise charges the first real
    request roughly 1.9s of one-time model/collection init. Steady-state retrieval is
    ~7ms, so paying this cost at startup keeps the first scan or chat as fast as the rest.
    """
    import asyncio

    def _prime() -> int:
        from app.services.vector_memory_service import vector_memory_service

        vector_memory_service.find_similar_memories(
            merchant_id="__warmup__",
            query_text="dormant vip recovery discount benchmark",
            top_k=1,
        )
        return vector_memory_service._collection.count()

    try:
        started = time.perf_counter()
        count = await asyncio.to_thread(_prime)
        print(f"[Warm-up] RAG ready in {time.perf_counter() - started:.2f}s ({count} memories indexed)")
    except Exception as err:
        print(f"[Warm-up] RAG pre-load skipped: {err}")


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
        from app.integrations.razorpay_client import razorpay_client
        _ = razorpay_client
        checks["razorpay"] = "✅ Configured"
    except Exception as e:
        checks["razorpay"] = f"❌ Error: {str(e)}"
    
    # LLM
    llm_configured = bool(settings.openrouter_api_key)
    checks["llm_service"] = "✅ Configured" if llm_configured else "⚠️ No API key"
    
    # Vector Memory
    try:
        from app.services.vector_memory_service import VectorMemoryService
        VectorMemoryService()
        checks["vector_memory"] = "✅ Ready"
    except Exception as e:
        checks["vector_memory"] = f"⚠️ Warning: {str(e)}"
    
    all_healthy = all("✅" in v for v in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/metrics")
async def metrics_endpoint() -> dict:
    """Returns application metrics in JSON format (Prometheus-compatible)."""
    from app.services.metrics_service import metrics_service
    from app.services.cache_service import query_cache_service
    from app.services.agent_performance_tracker import agent_performance_tracker
    
    return {
        "metrics": metrics_service.get_metrics(),
        "cache_stats": query_cache_service.get_stats(),
        "agent_stats": agent_performance_tracker.get_all_stats(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics/prometheus")
async def metrics_prometheus() -> str:
    """Returns metrics in Prometheus text format."""
    from app.services.metrics_service import metrics_service
    return metrics_service.export_prometheus_format()


@app.get("/metrics")
async def metrics_endpoint() -> dict:
    """Returns application metrics in JSON format (Prometheus-compatible)."""
    from app.services.metrics_service import metrics_service
    from app.services.cache_service import query_cache_service
    from app.services.agent_performance_tracker import agent_performance_tracker
    
    return {
        "metrics": metrics_service.get_metrics(),
        "cache_stats": query_cache_service.get_stats(),
        "agent_stats": agent_performance_tracker.get_all_stats(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/metrics/prometheus")
async def metrics_prometheus() -> str:
    """Returns metrics in Prometheus text format."""
    from app.services.metrics_service import metrics_service
    return metrics_service.export_prometheus_format()
