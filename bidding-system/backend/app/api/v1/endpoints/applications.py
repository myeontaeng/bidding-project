from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.bid_application import BidApplication, BidDocument
from app.models.document_template import DocumentTemplate
from app.schemas.bid_application import (
    BidApplicationCreate, BidApplicationRead,
    ReviewAction, DocumentTemplateCreate,
)
from app.services.bid_application import create_application, review_document, submit_application

router = APIRouter(tags=["applications"])


# ── 서류 템플릿 ──────────────────────────────────────────────────────────────
@router.get("/templates", response_model=list[dict])
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentTemplate))
    return [{"id": t.id, "name": t.name, "doc_type": t.doc_type} for t in result.scalars().all()]


@router.post("/templates", status_code=201)
async def create_template(body: DocumentTemplateCreate, db: AsyncSession = Depends(get_db)):
    import re
    placeholders = re.findall(r"\{\{(\w+)\}\}", body.content)
    t = DocumentTemplate(**body.model_dump(), placeholders=placeholders)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return {"id": t.id, "name": t.name, "doc_type": t.doc_type, "placeholders": t.placeholders}


# ── 입찰 지원 건 ─────────────────────────────────────────────────────────────
@router.get("/applications", response_model=list[BidApplicationRead])
async def list_applications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BidApplication).order_by(BidApplication.created_at.desc()))
    return list(result.scalars().all())


@router.post("/applications", response_model=BidApplicationRead, status_code=201)
async def create_application_endpoint(
    body: BidApplicationCreate, db: AsyncSession = Depends(get_db)
):
    return await create_application(db, body)


@router.get("/applications/{app_id}", response_model=BidApplicationRead)
async def get_application(app_id: int, db: AsyncSession = Depends(get_db)):
    app = await db.get(BidApplication, app_id)
    if not app:
        from fastapi import HTTPException
        raise HTTPException(404, "Not found")
    return app


@router.post("/applications/{app_id}/submit", response_model=BidApplicationRead)
async def submit(app_id: int, db: AsyncSession = Depends(get_db)):
    return await submit_application(db, app_id)


# ── 서류 검토/승인 ────────────────────────────────────────────────────────────
@router.post("/documents/{doc_id}/review", response_model=dict)
async def review(doc_id: int, body: ReviewAction, db: AsyncSession = Depends(get_db)):
    doc = await review_document(db, doc_id, body.action, body.note)
    return {
        "id": doc.id,
        "status": doc.status,
        "reviewed_at": doc.reviewed_at,
        "approved_at": doc.approved_at,
        "reviewer_note": doc.reviewer_note,
    }


@router.get("/documents/{doc_id}", response_model=dict)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    doc = await db.get(BidDocument, doc_id)
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(404, "Not found")
    return {
        "id": doc.id,
        "application_id": doc.application_id,
        "doc_type": doc.doc_type,
        "title": doc.title,
        "content": doc.content,
        "status": doc.status,
        "reviewer_note": doc.reviewer_note,
        "reviewed_at": doc.reviewed_at,
        "approved_at": doc.approved_at,
        "submitted_at": doc.submitted_at,
        "created_at": doc.created_at,
    }
