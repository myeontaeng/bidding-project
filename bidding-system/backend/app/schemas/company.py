from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    business_number: str
    ceo_name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    bank_account: str | None = None
    cert_serial: str | None = None
    business_types: str | None = None


class CompanyRead(BaseModel):
    id: int
    name: str
    business_number: str   # 복호화된 값
    ceo_name: str | None
    address: str | None
    phone: str | None
    email: str | None
    business_types: str | None
    active: bool

    model_config = {"from_attributes": True}
