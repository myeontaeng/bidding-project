from datetime import datetime
from sqlalchemy import String, Float, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AwardRecord(Base):
    """과거 낙찰 이력 - 공공데이터포털 + 나라장터 수집"""
    __tablename__ = "award_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bid_number: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    organization: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    region: Mapped[str | None] = mapped_column(String(100))
    base_price: Mapped[float | None] = mapped_column(Float)       # 예정가격
    award_price: Mapped[float | None] = mapped_column(Float)      # 낙찰가
    award_rate: Mapped[float | None] = mapped_column(Float)       # 낙찰률 (award/base)
    bid_count: Mapped[int | None] = mapped_column(Integer)        # 투찰 참가 업체 수
    awarded_company: Mapped[str | None] = mapped_column(String(200))
    award_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    source: Mapped[str] = mapped_column(String(50), default="g2b")
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PriceModel(Base):
    """학습된 ML 모델 메타데이터"""
    __tablename__ = "price_models"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    version: Mapped[str] = mapped_column(String(50))
    category: Mapped[str | None] = mapped_column(String(100))   # None = 전체
    model_path: Mapped[str] = mapped_column(String(500))        # joblib 파일 경로
    train_count: Mapped[int] = mapped_column(Integer)           # 학습 데이터 건수
    mae: Mapped[float | None] = mapped_column(Float)            # Mean Absolute Error
    feature_importance: Mapped[dict | None] = mapped_column(JSON)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(default=True)
