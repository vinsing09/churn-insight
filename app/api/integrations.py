from fastapi import APIRouter

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("")
async def list_integrations():
    return {"message": "not implemented"}


@router.post("/typeform/connect")
async def typeform_connect():
    return {"message": "not implemented"}


@router.get("/typeform/callback")
async def typeform_callback():
    return {"message": "not implemented"}


@router.post("/typeform/sync")
async def typeform_sync():
    return {"message": "not implemented"}


@router.post("/delighted/connect")
async def delighted_connect():
    return {"message": "not implemented"}


@router.post("/delighted/sync")
async def delighted_sync():
    return {"message": "not implemented"}
