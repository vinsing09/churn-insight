from fastapi import APIRouter

router = APIRouter(prefix="/account", tags=["account"])


@router.get("")
async def get_account():
    return {"message": "not implemented"}


@router.put("")
async def update_account():
    return {"message": "not implemented"}


@router.put("/ad-copy")
async def update_ad_copy():
    return {"message": "not implemented"}
