from fastapi import APIRouter

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("")
async def list_themes():
    return {"message": "not implemented"}


@router.get("/{theme_id}")
async def get_theme(theme_id: str):
    return {"message": "not implemented"}


@router.get("/{theme_id}/responses")
async def get_theme_responses(theme_id: str):
    return {"message": "not implemented"}
