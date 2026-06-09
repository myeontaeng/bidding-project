from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password, verify_password, create_access_token, get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User, ROLE_ADMIN, ROLE_PARTNER
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(access_token=create_access_token(user.username))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """새 사용자 등록 — 관리자 전용"""
    if body.role not in (ROLE_ADMIN, ROLE_PARTNER):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "role은 admin 또는 partner")
    exists = await db.scalar(select(User.id).where(User.username == body.username))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 사용 중인 사용자명입니다")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
        is_admin=(body.role == ROLE_ADMIN),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
