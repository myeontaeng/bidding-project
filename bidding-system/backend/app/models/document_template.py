from datetime import datetime
from sqlalchemy import String, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DocumentTemplate(Base):
    """서류 템플릿 - 플레이스홀더를 회사 정보로 치환"""
    __tablename__ = "document_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))          # 예: 입찰참가신청서
    doc_type: Mapped[str] = mapped_column(String(100))      # bid_application, proposal, price_breakdown
    content: Mapped[str] = mapped_column(Text)              # 템플릿 본문 ({{company_name}} 등 플레이스홀더)
    placeholders: Mapped[list | None] = mapped_column(JSON) # 사용된 플레이스홀더 목록
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
