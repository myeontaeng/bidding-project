from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.bid_application import BidApplication, BidDocument
from app.models.announcement import Announcement
from app.models.document_template import DocumentTemplate
from app.schemas.bid_application import BidApplicationCreate
from app.services.company import get_company, get_company_raw
from app.services.document_ai import identify_required_docs, generate_document_draft
from app.services.audit import log_audit


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def create_application(db: AsyncSession, data: BidApplicationCreate) -> BidApplication:
    ann = await db.get(Announcement, data.announcement_id)
    if not ann:
        raise HTTPException(404, "Announcement not found")

    company = await get_company(db, data.company_id)
    if not company:
        raise HTTPException(404, "Company not found")

    # 필요 서류 자동 식별
    required_docs = await identify_required_docs(ann.title, ann.title)

    app = BidApplication(
        announcement_id=data.announcement_id,
        company_id=data.company_id,
        status="in_progress",
        required_docs=required_docs,
        bid_price=data.bid_price,
        notes=data.notes,
    )
    db.add(app)
    await db.flush()

    # 각 서류 초안 자동 생성
    ann_info = {
        "title": ann.title,
        "organization": ann.organization,
        "bid_number": ann.bid_number,
        "deadline": ann.deadline,
    }

    for doc_type in required_docs:
        template = await db.scalar(
            select(DocumentTemplate).where(DocumentTemplate.doc_type == doc_type)
        )
        content = await generate_document_draft(
            doc_type=doc_type,
            company_info=company,
            announcement_info=ann_info,
            template_content=template.content if template else None,
        )
        doc = BidDocument(
            application_id=app.id,
            doc_type=doc_type,
            title=f"{ann.title} - {doc_type}",
            content=content,
            status="draft",
        )
        db.add(doc)

    await log_audit(db, "application", app.id, "created",
                    details={"announcement_id": data.announcement_id, "company_id": data.company_id})
    await db.commit()
    await db.refresh(app)
    return app


async def review_document(
    db: AsyncSession, doc_id: int, action: str, note: str | None
) -> BidDocument:
    doc = await db.get(BidDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc.status not in ("draft", "review", "rejected"):
        raise HTTPException(400, f"Cannot review document in status '{doc.status}'")

    doc.reviewer_note = note
    doc.reviewed_at = _now()

    if action == "approve":
        doc.status = "approved"
        doc.approved_at = _now()
    elif action == "reject":
        doc.status = "rejected"
    else:
        raise HTTPException(400, "action must be 'approve' or 'reject'")

    # 서류 상태 변경에 따라 입찰 지원 상태 자동 갱신
    app = await db.get(BidApplication, doc.application_id)
    if app and app.status not in ("submitted", "won", "lost", "cancelled"):
        if action == "reject":
            app.status = "rejected"
        elif action == "approve":
            other_rejected = any(
                d.status == "rejected"
                for d in app.documents
                if d.id != doc.id
            )
            if not other_rejected:
                app.status = "in_progress"

    await log_audit(db, "application", doc.application_id,
                    f"doc_{action}d", details={"doc_id": doc.id, "doc_type": doc.doc_type, "note": note})
    await db.commit()
    await db.refresh(doc)
    return doc


async def cancel_application(db: AsyncSession, app_id: int) -> BidApplication:
    app = await db.get(BidApplication, app_id)
    if not app:
        raise HTTPException(404, "Application not found")
    if app.status in ("submitted", "won", "lost"):
        raise HTTPException(400, f"제출 완료/결과 확정 건은 취소할 수 없습니다 (현재 상태: {app.status})")
    app.status = "cancelled"
    await log_audit(db, "application", app.id, "cancelled", details={})
    await db.commit()
    await db.refresh(app)
    return app


async def submit_application(db: AsyncSession, app_id: int) -> BidApplication:
    """
    HITL: 모든 서류 승인 확인 후 제출 상태로 전환.
    실제 전자서명·공동인증서 처리는 담당자 수동 진행.
    """
    app = await db.get(BidApplication, app_id)
    if not app:
        raise HTTPException(404, "Application not found")

    unapproved = [d for d in app.documents if d.status != "approved"]
    if unapproved:
        raise HTTPException(
            400,
            f"미승인 서류 {len(unapproved)}건 있음. 모든 서류 승인 후 제출 가능."
        )

    app.status = "submitted"
    app.submitted_at = _now()
    for doc in app.documents:
        doc.status = "submitted"
        doc.submitted_at = _now()

    await log_audit(db, "application", app.id, "submitted",
                    details={"bid_price": app.bid_price})
    await db.commit()
    await db.refresh(app)
    return app
