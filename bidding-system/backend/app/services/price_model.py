"""LightGBM 기반 낙찰가 예측 모델"""
import logging
import os
import joblib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.award_record import AwardRecord, PriceModel

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

CATEGORY_MAP = {
    "IT서비스": 0, "소프트웨어": 1, "건설": 2,
    "용역": 3, "물품구매": 4, "시설공사": 5,
}
REGION_MAP = {
    "서울": 0, "경기": 1, "부산": 2, "인천": 3,
    "대구": 4, "광주": 5, "대전": 6, "울산": 7, "세종": 8,
}


def _build_features(records: list[AwardRecord]) -> tuple:
    """피처 행렬 + 타깃 벡터 생성"""
    X, y = [], []
    for r in records:
        if r.base_price is None or r.award_rate is None:
            continue
        X.append([
            float(r.base_price),
            float(CATEGORY_MAP.get(r.category or "", -1) + 1),
            float(REGION_MAP.get(r.region or "", -1) + 1),
            float(r.bid_count or 5),
            float(r.award_date.month if r.award_date else 6),
        ])
        y.append(float(r.award_rate))
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


async def train_model(db: AsyncSession, category: str | None = None) -> dict:
    """LightGBM 학습 - 데이터 부족 시 Ridge로 fallback"""
    stmt = select(AwardRecord).where(AwardRecord.award_rate.isnot(None))
    if category:
        stmt = stmt.where(AwardRecord.category == category)

    records = list((await db.execute(stmt)).scalars().all())
    if len(records) < 10:
        return {"error": f"Not enough data: {len(records)} records"}

    X, y = _build_features(records)
    if len(X) < 10:
        return {"error": "Not enough valid features"}

    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]

    try:
        import lightgbm as lgb
        model = lgb.LGBMRegressor(
            n_estimators=200, learning_rate=0.05, num_leaves=31,
            min_child_samples=5, random_state=42, verbose=-1,
        )
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], callbacks=[lgb.early_stopping(20, verbose=False)])
        fi = dict(zip(["base_price", "category", "region", "bid_count", "month"],
                      model.feature_importances_.tolist()))
    except Exception as e:
        logger.warning("LightGBM failed (%s), fallback to Ridge", e)
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        model = Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
        model.fit(X_train, y_train)
        fi = {}

    y_pred = model.predict(X_val)
    mae = float(np.mean(np.abs(y_pred - y_val)))

    version = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = str(MODEL_DIR / f"price_model_{version}.joblib")
    joblib.dump(model, path)

    # 기존 active 모델 비활성화
    existing = list((await db.execute(
        select(PriceModel).where(PriceModel.active == True, PriceModel.category == category)
    )).scalars().all())
    for m in existing:
        m.active = False

    pm = PriceModel(
        version=version,
        category=category,
        model_path=path,
        train_count=len(X),
        mae=round(mae, 4),
        feature_importance=fi,
        active=True,
    )
    db.add(pm)
    await db.commit()

    logger.info("Model trained: version=%s mae=%.4f count=%d", version, mae, len(X))
    return {"version": version, "mae": round(mae, 4), "train_count": len(X), "feature_importance": fi}


async def _load_active_model(db: AsyncSession, category: str | None = None):
    # category-specific model 먼저, 없으면 global model(category=None)
    for cat in [category, None]:
        pm = await db.scalar(
            select(PriceModel)
            .where(PriceModel.active == True, PriceModel.category == cat)
            .order_by(PriceModel.trained_at.desc())
        )
        if pm and os.path.exists(pm.model_path):
            return joblib.load(pm.model_path), pm
    return None, None


async def predict_award_rate(
    db: AsyncSession,
    base_price: float,
    category: str | None,
    region: str | None,
    bid_count: int = 8,
) -> dict:
    """단일 공고에 대한 낙찰률 예측 + 추천 범위"""
    model, pm = await _load_active_model(db, category)

    # 학습된 모델 없으면 통계 기반 fallback
    if model is None:
        return _stat_based_recommendation(base_price)

    month = datetime.now(timezone.utc).month
    X = np.array([[
        base_price,
        float(CATEGORY_MAP.get(category or "", -1) + 1),
        float(REGION_MAP.get(region or "", -1) + 1),
        float(bid_count),
        float(month),
    ]], dtype=np.float32)

    predicted_rate = float(model.predict(X)[0])
    predicted_rate = max(0.80, min(0.99, predicted_rate))

    # 추천 범위: 예측값 ±1.5%
    low = max(0.80, predicted_rate - 0.015)
    high = min(0.99, predicted_rate + 0.015)

    return {
        "predicted_rate": round(predicted_rate, 4),
        "recommended_range": {"low": round(low, 4), "high": round(high, 4)},
        "recommended_price_low": round(base_price * low, -3),
        "recommended_price_high": round(base_price * high, -3),
        "model_version": pm.version if pm else None,
        "model_mae": pm.mae if pm else None,
    }


def _stat_based_recommendation(base_price: float) -> dict:
    """모델 없을 때 통계 기반 추천 (평균 낙찰률 90.5%)"""
    mean_rate = 0.905
    low, high = 0.890, 0.920
    return {
        "predicted_rate": mean_rate,
        "recommended_range": {"low": low, "high": high},
        "recommended_price_low": round(base_price * low, -3),
        "recommended_price_high": round(base_price * high, -3),
        "model_version": "stat_fallback",
        "model_mae": None,
    }
