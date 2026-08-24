from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_database_session
from app.simulator.simulation_orchestrator import run_full_merchant_simulation
from app.services.snapshot_storage_service import snapshot_storage_service
from app.services.trace_logger_service import trace_logger_service

router = APIRouter(prefix="/simulator", tags=["Merchant Data Simulator"])


@router.post("/generate")
async def generate_merchant_data(
    merchant_name: str = "StyleKart",
    customer_count: int = 500,
    order_count: int = 2000,
    session_id: str | None = None,
    session: AsyncSession = Depends(get_database_session),
) -> dict:
    """Generates synthetic merchant data, enriches profiles, saves local snapshot and logs trace."""
    result = await run_full_merchant_simulation(
        session=session,
        merchant_name=merchant_name,
        customer_count=customer_count,
        order_count=order_count,
    )
    
    step_data = {
        "merchant_id": result["merchant_id"],
        "merchant_name": result["merchant_name"],
        "customers_created": result["customers_created"],
        "orders_created": result["orders_created"],
        "segment_distribution": result["segment_distribution"],
    }

    trace_logger_service.log_trace_step(
        run_id=result["merchant_id"],
        session_id=session_id,
        step_name="1_dataset_generation",
        step_data=step_data,
    )
    if session_id:
        trace_logger_service.log_trace_step(
            run_id=session_id,
            session_id=session_id,
            step_name="1_dataset_generation",
            step_data=step_data,
        )

    return {
        "status": "success",
        "message": f"Generated {result['customers_created']} customers with enriched profiles",
        "data": result,
    }


@router.get("/local-snapshot")
async def get_local_simulation_snapshot() -> dict:
    """Retrieves the latest generated merchant dataset from local JSON storage."""
    snapshot = snapshot_storage_service.get_latest_snapshot()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No local simulation snapshot found. Run generator first.")
    return {"status": "success", "data": snapshot}


@router.post("/load-from-local")
async def load_from_local_json(
    session_id: str | None = None,
) -> dict:
    """Loads the existing local dataset from data/latest_simulation.json for analysis."""
    snapshot = snapshot_storage_service.get_latest_snapshot()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No local simulation snapshot found. Run generator first.")

    step_data = {
        "merchant_id": snapshot.get("merchant_id"),
        "merchant_name": snapshot.get("merchant_name"),
        "customers_created": snapshot.get("customers_created"),
        "orders_created": snapshot.get("orders_created"),
        "segment_distribution": snapshot.get("segment_distribution"),
    }
    if snapshot.get("merchant_id"):
        trace_logger_service.log_trace_step(
            run_id=snapshot["merchant_id"],
            session_id=session_id,
            step_name="1_dataset_generation",
            step_data=step_data,
        )
    if session_id:
        trace_logger_service.log_trace_step(
            run_id=session_id,
            session_id=session_id,
            step_name="1_dataset_generation",
            step_data=step_data,
        )

    return {
        "status": "success",
        "message": "Local dataset successfully loaded for analysis",
        "data": snapshot,
    }
