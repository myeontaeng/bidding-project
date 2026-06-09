import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db, AsyncSessionLocal
from app.api.v1.router import router
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from app.core.auth import seed_admin_user
    from app.services.award_collector import collect_award_records
    from app.services.price_model import train_model
    from app.services.seed_demo import seed_demo_data
    from app.models.award_record import PriceModel
    from sqlalchemy import select, func
    from app.services.announcement import backfill_deadlines, close_expired_announcements
    try:
        from backfill_new_fields import backfill as _backfill_new_fields
    except ImportError:
        _backfill_new_fields = None
    async with AsyncSessionLocal() as db:
        await seed_admin_user(db)
        # deadline NULL 소급 복구 (크롤러 버그 수정 이전 데이터)
        fixed = await backfill_deadlines(db)
        if fixed:
            logging.getLogger(__name__).info("Backfilled %d NULL deadlines from raw_data", fixed)
        # 새 필드(ministry, support_type 등) 소급 추출
        if _backfill_new_fields:
            new_fixed = await _backfill_new_fields(db)
            if new_fixed:
                logging.getLogger(__name__).info("Backfilled new fields for %d announcements", new_fixed)
        closed = await close_expired_announcements(db)
        if closed:
            logging.getLogger(__name__).info("Auto-closed %d expired announcements on startup", closed)
        # P3: 낙찰 이력 없으면 시드 데이터 수집
        await collect_award_records(db)
        # P3: 학습된 모델 없으면 자동 학습
        active_model = await db.scalar(
            select(func.count()).select_from(PriceModel).where(PriceModel.active == True)
        )
        if not active_model:
            await train_model(db)
        # P4: 입찰 실적 없으면 대시보드 데모 데이터 생성
        seeded = await seed_demo_data(db)
        if seeded:
            logging.getLogger(__name__).info("Demo data seeded: %d applications", seeded)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="입찰 자동화 시스템", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
