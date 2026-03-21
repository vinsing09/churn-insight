from fastapi import APIRouter

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.get("")
async def list_briefs():
    return {"message": "not implemented"}


@router.post("/generate")
async def generate_brief():
    return {"message": "not implemented"}


@router.get("/{brief_id}")
async def get_brief(brief_id: str):
    return {"message": "not implemented"}
