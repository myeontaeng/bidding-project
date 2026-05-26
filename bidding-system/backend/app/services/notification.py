"""알림 발송: Slack Webhook, 이메일(AWS SES)"""
import asyncio
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_slack(message: str) -> bool:
    if not settings.SLACK_WEBHOOK_URL:
        logger.debug("Slack webhook not configured, skip")
        return False
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(settings.SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
            res.raise_for_status()
        return True
    except Exception as e:
        logger.error("Slack send failed: %s", e)
        return False


def _build_announcement_message(announcement: dict) -> str:
    deadline = announcement.get("deadline")
    dday = announcement.get("dday")
    dday_str = f" (D-{dday})" if dday is not None else ""
    budget = announcement.get("budget")
    budget_str = f"{budget:,.0f}원" if budget else "미정"

    return (
        f"[신규 입찰 공고]{dday_str}\n"
        f"• 공고번호: {announcement.get('bid_number', '')}\n"
        f"• 제목: {announcement.get('title', '')}\n"
        f"• 발주처: {announcement.get('organization', '')}\n"
        f"• 예산: {budget_str}\n"
        f"• 마감: {deadline}\n"
        f"• 링크: {announcement.get('source_url', '')}"
    )


async def notify_new_announcement(announcement: dict, email: str | None = None, slack: bool = False):
    message = _build_announcement_message(announcement)
    if slack:
        await send_slack(message)
    if email:
        await send_email(email, f"[입찰공고] {announcement.get('title', '')}", message)


async def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.AWS_SES_ACCESS_KEY:
        logger.debug("SES not configured, skip email to %s", to)
        return False
    try:
        import boto3

        def _send():
            client = boto3.client(
                "ses",
                region_name=settings.AWS_SES_REGION,
                aws_access_key_id=settings.AWS_SES_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SES_SECRET_KEY,
            )
            client.send_email(
                Source=settings.NOTIFICATION_EMAIL_FROM,
                Destination={"ToAddresses": [to]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )

        await asyncio.to_thread(_send)
        return True
    except Exception as e:
        logger.error("Email send failed: %s", e)
        return False
