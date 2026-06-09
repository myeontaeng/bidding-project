from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password, get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User, ROLE_ADMIN, ROLE_PARTNER
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = list((await db.execute(select(User).order_by(User.created_at))).scalars().all())
    return users


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    if body.role not in (ROLE_ADMIN, ROLE_PARTNER):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "role은 admin 또는 partner")
    exists = await db.scalar(select(User.id).where(User.username == body.username))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 사용 중인 사용자명입니다")
    if not body.password or len(body.password) < 4:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "비밀번호는 4자 이상")
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


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "사용자 없음")
    if body.role is not None:
        if body.role not in (ROLE_ADMIN, ROLE_PARTNER):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "role은 admin 또는 partner")
        user.role = body.role
        user.is_admin = (body.role == ROLE_ADMIN)
    if body.password is not None:
        if len(body.password) < 4:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "비밀번호는 4자 이상")
        user.hashed_password = hash_password(body.password)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "사용자 없음")
    if user.id == current_user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "본인 계정은 삭제할 수 없습니다")
    await db.delete(user)
    await db.commit()
