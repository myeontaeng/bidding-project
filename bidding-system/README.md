# 입찰 자동화 시스템

나라장터 공고 수집 · 필터링 · 알림 · 서류 자동생성 · 가격 분석 · 실적 대시보드

## 빠른 시작

### 백엔드

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # 환경변수 편집 (ADMIN_PASSWORD 필수)
python start.py
```

로그인: `POST /api/v1/auth/login` → `{"username": "admin", "password": "..."}`  
이후 모든 요청 헤더에 `Authorization: Bearer <token>` 추가.

서버: http://localhost:8000  
API 문서: http://localhost:8000/docs

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

앱: http://localhost:3000

## 환경변수 (.env)

| 변수 | 설명 | 필수 |
|------|------|------|
| `DATABASE_URL` | SQLite 경로 | ✓ |
| `ENCRYPTION_KEY` | AES-256-GCM 32바이트 base64url 키 (`python -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`) | ✓ |
| `G2B_API_KEY` | 나라장터 OpenAPI 키 (data.go.kr) | |
| `JWT_SECRET` | JWT 서명 시크릿 (32자 이상 랜덤) | ✓ |
| `JWT_EXPIRE_MINUTES` | JWT 만료 시간 분 (기본: 1440) | |
| `ADMIN_USERNAME` | 관리자 계정명 (기본: admin) | |
| `ADMIN_PASSWORD` | 관리자 초기 비밀번호 — 기동 시 계정 자동 생성 | ✓ |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | |
| `AWS_SES_ACCESS_KEY` | AWS SES 이메일 발송 키 | |
| `AWS_SES_SECRET_KEY` | AWS SES 시크릿 | |
| `AWS_SES_REGION` | SES 리전 (기본: ap-northeast-2) | |
| `NOTIFICATION_EMAIL_FROM` | 발송 이메일 주소 | |
| `KAKAO_API_KEY` | 카카오 REST API 키 | |
| `KAKAO_SENDER_KEY` | 카카오 플러스친구 발신 프로필 키 | |
| `KAKAO_TEMPLATE_CODE` | 카카오 알림톡 템플릿 코드 | |
| `OPENAI_API_KEY` | 서류 AI 생성 (Phase 2) | |
| `CRAWL_INTERVAL_MINUTES` | 크롤링 주기 분 (기본: 30) | |

## 구현 현황

### Phase 1 — 공고 수집 · 알림
| 기능 | 파일 |
|------|------|
| DB 모델 (공고, 필터) | `app/models/` |
| 나라장터 Playwright 크롤러 | `app/crawlers/g2b_crawler.py` |
| 공고 검색 API | `app/api/v1/endpoints/announcements.py` |
| 필터 설정 CRUD | `app/api/v1/endpoints/filters.py` |
| Slack / AWS SES 이메일 알림 | `app/services/notification.py` |
| D-day 리마인더 | `app/services/announcement.py` |
| 스케줄러 (30분 크롤, 09:00 리마인더) | `app/services/scheduler.py` |

### Phase 2 — 서류 자동생성 · 승인 워크플로우
| 기능 | 파일 |
|------|------|
| 회사 정보 관리 | `app/models/company.py`, `app/api/v1/endpoints/companies.py` |
| 입찰 지원 관리 | `app/models/bid_application.py`, `app/api/v1/endpoints/applications.py` |
| OpenAI 서류 초안 생성 | `app/services/document_ai.py` |
| 검토 / 승인 워크플로우 | `app/services/bid_application.py` |

### Phase 3 — 가격 분석 · ML 추천
| 기능 | 파일 |
|------|------|
| 낙찰 이력 수집 | `app/services/award_collector.py` |
| LightGBM 투찰율 예측 | `app/services/price_model.py` |
| 가격 추천 / 시뮬레이션 | `app/services/price_advisor.py` |
| 가격 API | `app/api/v1/endpoints/price.py` |

### Phase 4 — 실적 대시보드 · 내보내기
| 기능 | 파일 |
|------|------|
| KPI · 월별 · 발주처별 통계 | `app/services/dashboard.py` |
| 유찰 원인 분석 | `app/services/result_tracker.py` |
| CSV / Excel 내보내기 | `app/services/export_service.py` |

## 기술 스택

- **백엔드**: FastAPI · SQLAlchemy (async) · APScheduler · Playwright
- **ML**: scikit-learn · LightGBM · joblib
- **AI**: OpenAI GPT (서류 초안)
- **알림**: Slack Webhook · AWS SES
- **프론트엔드**: Next.js 16 · React 19 · Tailwind CSS v4 · Recharts
- **DB**: SQLite (aiosqlite) — 프로덕션 시 PostgreSQL 권장

## 미결 사항 (need_edit.md)

착수 전 확정 필요한 비즈니스 결정 사항은 `../need_edit.md` 참조.
