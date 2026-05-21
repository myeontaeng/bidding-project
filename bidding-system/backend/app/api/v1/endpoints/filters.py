from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.filter_config import FilterConfig
from app.schemas.filter_config import FilterConfigCreate, FilterConfigRead

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("", response_model=list[FilterConfigRead])
async def list_filters(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FilterConfig))
    return list(result.scalars().all())


@router.post("", response_model=FilterConfigRead, status_code=201)
async def create_filter(body: FilterConfigCreate, db: AsyncSession = Depends(get_db)):
    fc = FilterConfig(**body.model_dump())
    db.add(fc)
    await db.commit()
    await db.refresh(fc)
    return fc


@router.delete("/{filter_id}", status_code=204)
async def delete_filter(filter_id: int, db: AsyncSession = Depends(get_db)):
    fc = await db.get(FilterConfig, filter_id)
    if fc:
        await db.delete(fc)
        await db.commit()
