from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
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


@router.get("/expiring-certs")
async def expiring_certs(days: int = Query(90), db: AsyncSession = Depends(get_db)):
    """만료 임박 인증서 목록 (기본 90일 이내)."""
    companies = await list_companies(db)
    today = date.today()
    cutoff = today + timedelta(days=days)
    result = []
    for c in companies:
        for cert in (c.get("certifications") or []):
            try:
                exp = date.fromisoformat(cert["expiry_date"])
                days_left = (exp - today).days
                if days_left <= days:
                    result.append({
                        "company_id": c["id"],
                        "company_name": c["name"],
                        "cert_name": cert["name"],
                        "cert_type": cert.get("cert_type"),
                        "expiry_date": cert["expiry_date"],
                        "days_remaining": days_left,
                        "expired": days_left < 0,
                    })
            except (KeyError, ValueError):
                continue
    result.sort(key=lambda x: x["days_remaining"])
    return result
