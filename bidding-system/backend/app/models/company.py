from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Company(Base):
    """회사 마스터 데이터 - 민감 필드는 암호화 저장"""
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    business_number: Mapped[str] = mapped_column(String(500))   # 암호화
    ceo_name: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(200))
    bank_account: Mapped[str | None] = mapped_column(String(500))   # 암호화
    cert_serial: Mapped[str | None] = mapped_column(String(500))    # 공동인증서 일련번호, 암호화
    business_types: Mapped[str | None] = mapped_column(Text)        # 업종 목록 (콤마 구분)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
