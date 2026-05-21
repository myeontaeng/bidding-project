"""OpenAI 기반 서류 분석 및 초안 생성"""
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

DOC_TYPES = {
    "bid_application": "입찰참가신청서",
    "proposal": "제안서",
    "price_breakdown": "가격산출내역서",
    "company_profile": "회사소개서",
    "cert_capability": "역량확인서",
}

# 키워드 기반 서류 식별 (OpenAI 없을 때 fallback)
_KEYWORD_RULES: list[tuple[list[str], str]] = [
    (["제안", "기술"], "proposal"),
    (["가격", "원가", "산출"], "price_breakdown"),
    (["회사소개", "사업실적"], "company_profile"),
    (["역량", "인증", "자격"], "cert_capability"),
]


def _keyword_identify(title: str, content: str) -> list[str]:
    text = (title + " " + content).lower()
    docs = {"bid_application"}  # 항상 필요
    for keywords, doc_type in _KEYWORD_RULES:
        if any(kw in text for kw in keywords):
            docs.add(doc_type)
    return list(docs)


async def identify_required_docs(title: str, announcement_content: str) -> list[str]:
    """공고 분석 → 필요 서류 목록 반환"""
    if not settings.OPENAI_API_KEY:
        logger.debug("OpenAI key not set, using keyword fallback")
        return _keyword_identify(title, announcement_content)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        doc_list = "\n".join(f"- {k}: {v}" for k, v in DOC_TYPES.items())
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "입찰 공고를 분석해 필요한 서류 유형을 선택하세요. "
                        f"가능한 서류:\n{doc_list}\n"
                        "필요한 서류의 key를 쉼표로만 구분해 반환하세요. 다른 텍스트 없이."
                    ),
                },
                {"role": "user", "content": f"공고 제목: {title}\n내용: {announcement_content[:1000]}"},
            ],
            max_tokens=100,
        )
        keys = [k.strip() for k in response.choices[0].message.content.split(",")]
        valid = [k for k in keys if k in DOC_TYPES]
        if "bid_application" not in valid:
            valid.insert(0, "bid_application")
        return valid
    except Exception as e:
        logger.error("OpenAI identify failed: %s, fallback to keyword", e)
        return _keyword_identify(title, announcement_content)


async def generate_document_draft(
    doc_type: str,
    company_info: dict,
    announcement_info: dict,
    template_content: str | None = None,
) -> str:
    """서류 초안 생성: 템플릿 + LLM"""
    # 1. 템플릿 플레이스홀더 치환
    if template_content:
        draft = template_content
        replacements = {
            "{{company_name}}": company_info.get("name", ""),
            "{{business_number}}": company_info.get("business_number", ""),
            "{{ceo_name}}": company_info.get("ceo_name", ""),
            "{{address}}": company_info.get("address", ""),
            "{{phone}}": company_info.get("phone", ""),
            "{{email}}": company_info.get("email", ""),
            "{{announcement_title}}": announcement_info.get("title", ""),
            "{{organization}}": announcement_info.get("organization", ""),
            "{{bid_number}}": announcement_info.get("bid_number", ""),
            "{{deadline}}": str(announcement_info.get("deadline", "")),
        }
        for placeholder, value in replacements.items():
            draft = draft.replace(placeholder, value or "")
        return draft

    # 2. OpenAI로 초안 생성 (템플릿 없을 때)
    if not settings.OPENAI_API_KEY:
        return _fallback_draft(doc_type, company_info, announcement_info)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        doc_name = DOC_TYPES.get(doc_type, doc_type)
        prompt = (
            f"다음 정보를 바탕으로 {doc_name} 초안을 작성해주세요.\n\n"
            f"회사명: {company_info.get('name')}\n"
            f"사업자번호: {company_info.get('business_number')}\n"
            f"대표자: {company_info.get('ceo_name')}\n\n"
            f"입찰 공고: {announcement_info.get('title')}\n"
            f"발주처: {announcement_info.get('organization')}\n"
            f"공고번호: {announcement_info.get('bid_number')}\n"
        )
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "공공입찰 서류 전문가입니다. 한국어로 공식적인 서류 초안을 작성합니다."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("OpenAI generate failed: %s, fallback", e)
        return _fallback_draft(doc_type, company_info, announcement_info)


def _fallback_draft(doc_type: str, company: dict, announcement: dict) -> str:
    doc_name = DOC_TYPES.get(doc_type, doc_type)
    return (
        f"[{doc_name} 초안]\n\n"
        f"공고번호: {announcement.get('bid_number', '')}\n"
        f"공고명: {announcement.get('title', '')}\n"
        f"발주처: {announcement.get('organization', '')}\n\n"
        f"회사명: {company.get('name', '')}\n"
        f"사업자등록번호: {company.get('business_number', '')}\n"
        f"대표자: {company.get('ceo_name', '')}\n"
        f"주소: {company.get('address', '')}\n\n"
        f"[이하 내용을 직접 작성하거나 OPENAI_API_KEY를 설정하면 자동 생성됩니다]"
    )
