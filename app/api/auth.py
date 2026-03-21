from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register():
    return {"message": "not implemented"}


@router.post("/login")
async def login():
    return {"message": "not implemented"}


@router.get("/me")
async def me():
    return {"message": "not implemented"}
