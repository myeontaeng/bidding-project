from datetime import datetime
from sqlalchemy import String, JSON, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FilterConfig(Base):
    """사용자별 공고 필터 설정 - 알림 조건으로도 사용"""
    __tablename__ = "filter_configs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    keywords: Mapped[list | None] = mapped_column(JSON)       # 키워드 목록
    categories: Mapped[list | None] = mapped_column(JSON)     # 업종 목록
    regions: Mapped[list | None] = mapped_column(JSON)        # 지역 목록
    organizations: Mapped[list | None] = mapped_column(JSON)  # 발주처 목록
    budget_min: Mapped[float | None] = mapped_column()
    budget_max: Mapped[float | None] = mapped_column()
    notify_email: Mapped[str | None] = mapped_column(String(200))
    notify_slack: Mapped[bool] = mapped_column(Boolean, default=False)
    reminder_days: Mapped[list | None] = mapped_column(JSON, default=lambda: [7, 3, 1])
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
