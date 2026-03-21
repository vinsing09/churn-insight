from fastapi import APIRouter

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run")
async def run_analysis():
    return {"message": "not implemented"}


@router.get("/status")
async def get_status():
    return {"message": "not implemented"}


@router.get("/runs")
async def list_runs():
    return {"message": "not implemented"}
