from fastapi import APIRouter, Depends, HTTPException, Request
from app.schemas.user import UserCreate, UserOut
from app.controllers import user_controller
from app.db.connection import get_connection

router = APIRouter()


@router.post("/", response_model=UserOut)
async def create_user(user_in: UserCreate, conn=Depends(get_connection)):
    existing = await user_controller.get_user_by_email(conn, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    user = await user_controller.create_user(conn, user_in)
    return user


@router.get("/", response_model=list[UserOut])
async def list_users(conn=Depends(get_connection)):
    return await user_controller.list_users(conn)
