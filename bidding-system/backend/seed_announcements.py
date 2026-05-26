"""공개 입찰공고 데모 데이터 시드"""
import asyncio
from datetime import datetime, timedelta
import random

from app.core.database import init_db, AsyncSessionLocal
from app.models.announcement import Announcement
from sqlalchemy import select

ANNOUNCEMENTS = [
    ("서울특별시 노후 상수도관 교체 공사", "서울특별시 상수도사업본부", "공사", "서울", 2_800_000_000, 12),
    ("부산항 컨테이너 터미널 운영 시스템 고도화", "부산항만공사", "용역", "부산", 450_000_000, 8),
    ("국립중앙의료원 의료정보시스템 구축", "국립중앙의료원", "용역", "서울", 1_200_000_000, 15),
    ("인천국제공항 3단계 터미널 내부 마감공사", "인천국제공항공사", "공사", "인천", 5_600_000_000, 20),
    ("경기도 스마트 가로등 설치 사업", "경기도청", "물품", "경기", 320_000_000, 6),
    ("한국도로공사 고속도로 CCTV 유지관리 용역", "한국도로공사", "용역", "전국", 890_000_000, 10),
    ("서울시 공공자전거 시스템 유지보수", "서울특별시 도시교통실", "용역", "서울", 280_000_000, 5),
    ("대전시 자원회수시설 소각로 정비 공사", "대전광역시 자원순환사업소", "공사", "대전", 1_100_000_000, 9),
    ("한국전력공사 전력계통 감시제어시스템 구축", "한국전력공사", "용역", "전국", 3_200_000_000, 18),
    ("광주광역시 지능형 교통시스템 구축", "광주광역시", "용역", "광주", 670_000_000, 7),
    ("국방부 군 시설 냉난방 설비 교체", "국방부", "물품", "전국", 1_500_000_000, 14),
    ("경상남도 농촌 태양광 발전시설 설치", "경상남도청", "공사", "경남", 430_000_000, 11),
    ("한국수자원공사 댐 안전진단 용역", "한국수자원공사", "용역", "전국", 560_000_000, 8),
    ("서울시 지하철 9호선 역사 시설물 유지보수", "서울시메트로9호선", "용역", "서울", 750_000_000, 6),
    ("충청북도 농업기술원 연구시설 신축 공사", "충청북도", "공사", "충북", 980_000_000, 13),
    ("국토교통부 항공정보통신시스템 구축", "국토교통부", "용역", "전국", 2_100_000_000, 16),
    ("강원도 산불 감시 드론 시스템 도입", "강원도청", "물품", "강원", 240_000_000, 4),
    ("한국철도공사 KTX 전동차 부품 구매", "한국철도공사", "물품", "전국", 1_800_000_000, 7),
    ("부산시 해운대 해수욕장 시설 정비", "부산광역시 해운대구", "공사", "부산", 190_000_000, 5),
    ("한국환경공단 대기오염 측정망 유지관리", "한국환경공단", "용역", "전국", 420_000_000, 9),
    ("세종시 정부청사 에너지 효율화 사업", "세종특별자치시", "공사", "세종", 850_000_000, 12),
    ("교육부 국립대학 전산망 통합 구축", "교육부", "용역", "전국", 1_650_000_000, 15),
    ("제주도 스마트관광 플랫폼 개발", "제주특별자치도", "용역", "제주", 380_000_000, 6),
    ("국민건강보험공단 데이터센터 서버 구매", "국민건강보험공단", "물품", "전국", 920_000_000, 8),
    ("울산시 산업단지 환경오염 모니터링 시스템", "울산광역시", "용역", "울산", 310_000_000, 5),
]

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        from sqlalchemy import func
        open_count = await db.scalar(
            select(func.count()).select_from(Announcement).where(Announcement.status == "open")
        )
        if open_count and open_count > 0:
            print(f"open 공고 {open_count}건 이미 존재 - 시드 생략")
            return

        now = datetime.utcnow()
        items = []
        for i, (title, org, cat, region, budget, days) in enumerate(ANNOUNCEMENTS):
            bid_num = f"20260526-{i+1:04d}"
            deadline = now + timedelta(days=days + random.randint(-2, 3))
            published = now - timedelta(days=random.randint(1, 7))
            items.append(Announcement(
                bid_number=bid_num,
                title=title,
                organization=org,
                category=cat,
                region=region,
                budget=float(budget),
                deadline=deadline,
                published_at=published,
                source_url=f"https://www.g2b.go.kr/demo/{bid_num}",
                source="g2b",
                status="open",
                notified=False,
                reminders_sent=[],
                raw_data={"seeded": True},
            ))

        db.add_all(items)
        await db.commit()
        print(f"공고 {len(items)}건 시드 완료")

if __name__ == "__main__":
    asyncio.run(main())
