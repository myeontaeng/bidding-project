from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreate
from app.core.crypto import encrypt, decrypt


def _encrypt_company(data: dict) -> dict:
    for field in ("business_number", "bank_account", "cert_serial"):
        if data.get(field):
            data[field] = encrypt(data[field])
    return data


def _safe_decrypt(value: str | None) -> str:
    if not value:
        return ""
    try:
        return decrypt(value)
    except Exception:
        return value  # plaintext (legacy / seed data)


def _decrypt_company(c: Company) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "business_number": _safe_decrypt(c.business_number),
        "ceo_name": c.ceo_name,
        "address": c.address,
        "phone": c.phone,
        "email": c.email,
        "business_types": c.business_types,
        "active": c.active,
    }


async def create_company(db: AsyncSession, data: CompanyCreate) -> dict:
    raw = _encrypt_company(data.model_dump())
    company = Company(**raw)
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return _decrypt_company(company)


async def list_companies(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Company).where(Company.active == True))
    return [_decrypt_company(c) for c in result.scalars().all()]


async def get_company(db: AsyncSession, company_id: int) -> dict | None:
    c = await db.get(Company, company_id)
    if not c:
        return None
    return _decrypt_company(c)


async def get_company_raw(db: AsyncSession, company_id: int) -> Company | None:
    return await db.get(Company, company_id)
