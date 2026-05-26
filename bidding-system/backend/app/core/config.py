from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./bidding.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SLACK_WEBHOOK_URL: str = ""
    AWS_SES_ACCESS_KEY: str = ""
    AWS_SES_SECRET_KEY: str = ""
    AWS_SES_REGION: str = "ap-northeast-2"
    NOTIFICATION_EMAIL_FROM: str = "noreply@example.com"
    CRAWL_INTERVAL_MINUTES: int = 30
    OPENAI_API_KEY: str = ""
    ENCRYPTION_KEY: str = ""  # AES-256-GCM key (32-byte base64url) - generate: python -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"

    # 나라장터 OpenAPI (data.go.kr에서 발급)
    G2B_API_KEY: str = ""

    # JWT 인증
    JWT_SECRET: str = "change-this-in-production-use-random-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24시간

    # 최초 관리자 계정 (기동 시 없으면 자동 생성)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""  # 필수 설정 — 빈 값이면 자동 생성 건너뜀

    # 카카오 알림톡
    KAKAO_API_KEY: str = ""           # REST API 키
    KAKAO_SENDER_KEY: str = ""        # 플러스친구 발신 프로필 키
    KAKAO_TEMPLATE_CODE: str = ""     # 알림톡 템플릿 코드

    class Config:
        env_file = ".env"


settings = Settings()
