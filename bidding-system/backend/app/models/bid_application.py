from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BidApplication(Base):
    """입찰 지원 건 - 공고 + 회사를 연결"""
    __tablename__ = "bid_applications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    announcement_id: Mapped[int] = mapped_column(Integer, ForeignKey("announcements.id"))
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    # pending / in_progress / submitted / won / lost
    status: Mapped[str] = mapped_column(String(50), default="pending")
    required_docs: Mapped[list | None] = mapped_column(JSON)   # 식별된 필요 서류 목록
    bid_price: Mapped[float | None] = mapped_column()
    notes: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Phase 4: 결과 추적
    result: Mapped[str | None] = mapped_column(String(20))        # won / lost / pending
    result_price: Mapped[float | None] = mapped_column()          # 낙찰가 (낙찰 시)
    winner_price: Mapped[float | None] = mapped_column()          # 1위 낙찰가 (유찰 시 분석용)
    our_rank: Mapped[int | None] = mapped_column(Integer)         # 투찰 순위
    total_bidders: Mapped[int | None] = mapped_column(Integer)    # 총 투찰 업체 수
    loss_reason: Mapped[str | None] = mapped_column(Text)         # 유찰 원인 분석
    result_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    result_notified: Mapped[bool] = mapped_column(default=False)

    documents: Mapped[list["BidDocument"]] = relationship(  # noqa: F821
        "BidDocument", back_populates="application", lazy="selectin"
    )


class BidDocument(Base):
    """생성된 서류 - 검토/승인 워크플로우"""
    __tablename__ = "bid_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("bid_applications.id"))
    doc_type: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    # draft / review / approved / rejected / submitted
    status: Mapped[str] = mapped_column(String(50), default="draft")
    reviewer_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    application: Mapped["BidApplication"] = relationship(
        "BidApplication", back_populates="documents"
    )
