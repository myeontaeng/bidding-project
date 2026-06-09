from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def log_audit(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    action: str,
    actor: str = "system",
    details: dict | None = None,
) -> None:
    db.add(AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        details=details,
    ))
    # flush only — caller commits


async def get_audit_trail(
    db: AsyncSession, entity_type: str, entity_id: int
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(AuditLog.created_at.desc())
    )
    return list(result.scalars().all())
