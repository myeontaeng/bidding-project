from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.company import CompanyCreate, CompanyRead
from app.services.company import create_company, list_companies

router = APIRouter(prefix="/companies", tags=["companies"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[CompanyRead])
async def list_companies_endpoint(db: AsyncSession = Depends(get_db)):
    return await list_companies(db)


@router.post("", response_model=CompanyRead, status_code=201)
async def create_company_endpoint(body: CompanyCreate, db: AsyncSession = Depends(get_db)):
    return await create_company(db, body)
