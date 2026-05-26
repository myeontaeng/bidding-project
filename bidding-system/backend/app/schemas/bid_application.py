from datetime import datetime
from pydantic import BaseModel


class BidDocumentRead(BaseModel):
    id: int
    doc_type: str
    title: str
    content: str
    status: str
    reviewer_note: str | None
    reviewed_at: datetime | None
    approved_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BidApplicationCreate(BaseModel):
    announcement_id: int
    company_id: int
    bid_price: float | None = None
    notes: str | None = None


class BidApplicationRead(BaseModel):
    id: int
    announcement_id: int
    company_id: int
    status: str
    required_docs: list[str] | None
    bid_price: float | None
    notes: str | None
    submitted_at: datetime | None
    created_at: datetime
    documents: list[BidDocumentRead] = []
    result: str | None = None
    result_price: float | None = None
    winner_price: float | None = None
    our_rank: int | None = None
    total_bidders: int | None = None
    loss_reason: str | None = None

    model_config = {"from_attributes": True}


class ReviewAction(BaseModel):
    action: str    # approve | reject
    note: str | None = None


class DocumentTemplateCreate(BaseModel):
    name: str
    doc_type: str
    content: str
