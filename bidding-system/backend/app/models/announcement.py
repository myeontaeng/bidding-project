from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bid_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    organization: Mapped[str] = mapped_column(String(200), index=True)  # 발주처
    category: Mapped[str | None] = mapped_column(String(100), index=True)  # 업종
    region: Mapped[str | None] = mapped_column(String(100), index=True)  # 지역
    budget: Mapped[float | None] = mapped_column(Float)  # 예산
    deadline: Mapped[datetime | None] = mapped_column(DateTime, index=True)  # 마감일
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(50), default="g2b")  # g2b, etc.
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, closed
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
