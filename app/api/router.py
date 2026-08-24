from fastapi import APIRouter
from app.api.routes_simulator import router as simulator_router
from app.api.routes_customers import router as customers_router
from app.api.routes_growth import router as growth_router
from app.api.routes_campaigns import router as campaigns_router
from app.api.routes_experiments import router as experiments_router
from app.api.routes_webhooks import router as webhooks_router
from app.api.routes_sessions import router as sessions_router

api_router = APIRouter()
api_router.include_router(simulator_router)
api_router.include_router(customers_router)
api_router.include_router(growth_router)
api_router.include_router(campaigns_router)
api_router.include_router(experiments_router)
api_router.include_router(webhooks_router)
api_router.include_router(sessions_router)
