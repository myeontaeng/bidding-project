"""나라장터(g2b.go.kr) 입찰공고 크롤러 + data.go.kr OpenAPI 폴백"""
import logging
import urllib.parse
from datetime import datetime, timedelta

import httpx
from playwright.async_api import async_playwright, Page

from app.core.config import settings

logger = logging.getLogger(__name__)

_API_BASE = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
_API_OPERATIONS = [
    "getBidPblancListInfoThng",    # 물품
    "getBidPblancListInfoCnstwk",  # 공사
    "getBidPblancListInfoServc",   # 용역
]

_IT_KW = [
    "it서비스", "정보화", "전산", "ict", "소프트웨어", "sw개발", "시스템구축",
    "플랫폼", "빅데이터", "인공지능", "ai시스템", "디지털전환", "클라우드",
    "사이버보안", "정보보안", "네트워크구축", "데이터베이스",
]
_IT_PARTIAL = ["정보", "시스템", "소프트", "디지털", "데이터", "ai ", " ai", "플랫폼", "클라우드", "ict", "sw ", " sw"]


def _classify_category(title: str, operation: str | None = None) -> str:
    """제목 + API 오퍼레이션으로 업종 분류."""
    tl = title.lower()

    if operation == "getBidPblancListInfoCnstwk":
        if any(w in tl for w in ["건축", "신축", "증축", "리모델링", "인테리어"]):
            return "건축공사"
        if any(w in tl for w in ["토목", "도로", "교량", "하수도", "상수도", "항만"]):
            return "토목공사"
        if any(w in tl for w in ["전기", "통신공사", "소방", "기계설비"]):
            return "전기·통신공사"
        return "시설공사"

    if operation == "getBidPblancListInfoThng":
        if any(w in tl for w in ["it", "pc", "노트북", "서버", "네트워크장비", "전산"]):
            return "IT장비"
        return "물품구매"

    if operation == "getBidPblancListInfoServc":
        if any(w in tl for w in _IT_KW) or any(w in tl for w in _IT_PARTIAL):
            return "IT서비스"
        if any(w in tl for w in ["연구", "조사", "분석", "평가", "진단", "실태"]):
            return "연구용역"
        if any(w in tl for w in ["교육", "훈련", "컨설팅", "자문", "강의", "강사"]):
            return "교육·컨설팅"
        if any(w in tl for w in ["청소", "경비", "시설관리", "유지관리", "환경미화"]):
            return "시설관리"
        return "용역"

    # 오퍼레이션 미상 (Playwright 등) — 제목 기반 추론
    if any(w in tl for w in _IT_KW) or any(w in tl for w in _IT_PARTIAL):
        return "IT서비스"
    if any(w in tl for w in ["건설", "공사", "건축", "시공", "토목"]):
        return "건설공사"
    if any(w in tl for w in ["물품", "구매", "조달", "납품", "기자재"]):
        return "물품구매"
    return "용역"
_G2B_LIST_URL = "https://www.g2b.go.kr/ep/invitation/publish/bidPublishInfoList.do"
_DT_FMTS = ("%Y%m%d%H%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y%m%d")

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    for fmt in _DT_FMTS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _parse_api_item(item: dict, operation: str | None = None) -> dict | None:
    try:
        bid_number = (item.get("bidNtceNo") or "") + "-" + (item.get("bidNtceOrd") or "00")
        raw_budget = item.get("presmptPrce") or item.get("asignBdgtAmt")
        try:
            budget = float(raw_budget) if raw_budget else None
        except (ValueError, TypeError):
            budget = None
        source_url = (
            item.get("bidNtceDtlUrl")
            or (
                f"https://www.g2b.go.kr/link/PNPE027_01/single/"
                f"?bidPbancNo={item.get('bidNtceNo')}&bidPbancOrd={item.get('bidNtceOrd')}"
            )
        )
        raw_avail = item.get("asignBdgtAmt")
        try:
            budget_available = float(raw_avail) if raw_avail else None
        except (ValueError, TypeError):
            budget_available = None

        prtcpt = item.get("prtcptLmtYn")
        eligible: list | None = None
        if prtcpt == "Y":
            eligible = ["제한경쟁"]
        elif prtcpt == "N":
            eligible = ["일반경쟁"]

        title = item.get("bidNtceNm", "").strip()
        bid_method = item.get("bidMethdNm") or None

        return {
            "bid_number": bid_number,
            "title": title,
            "organization": item.get("dminsttNm", "").strip(),
            "ministry": (item.get("ntceInsttNm") or "").strip() or None,
            "category": _classify_category(title, operation),
            "support_type": bid_method,
            "budget": budget,
            "budget_available": budget_available,
            "eligible_institutions": eligible,
            "deadline": _parse_dt(item.get("bidClseDt")),
            "opening_date": _parse_dt(item.get("opengDt")),
            "published_at": _parse_dt(item.get("bidNtceDt") or item.get("rgstDt")) or datetime.utcnow(),
            "source_url": source_url,
            "source": "g2b",
            "raw_data": item,
        }
    except Exception as e:
        logger.warning("API item parse failed: %s", e)
        return None


async def _crawl_via_api(max_pages: int) -> list[dict]:
    """data.go.kr OpenAPI (조달청_나라장터입찰공고정보서비스 v2)"""
    results = []
    now = datetime.now()
    inqry_bgn = (now - timedelta(days=7)).strftime("%Y%m%d%H%M")
    inqry_end = now.strftime("%Y%m%d%H%M")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for operation in _API_OPERATIONS:
            url = f"{_API_BASE}/{operation}"
            for page_no in range(1, max_pages + 1):
                try:
                    resp = await client.get(
                        url,
                        params={
                            "serviceKey": settings.G2B_API_KEY,
                            "numOfRows": "100",
                            "pageNo": str(page_no),
                            "inqryDiv": "1",
                            "inqryBgnDt": inqry_bgn,
                            "inqryEndDt": inqry_end,
                            "type": "json",
                        },
                    )
                    resp.raise_for_status()
                    body = resp.json().get("response", {}).get("body", {})
                    items = body.get("items") or []
                    if isinstance(items, dict):
                        items = [items]
                    for raw in items:
                        parsed = _parse_api_item(raw, operation)
                        if parsed:
                            results.append(parsed)
                    total = int(body.get("totalCount") or 0)
                    if page_no * 100 >= total or not items:
                        break
                except Exception as e:
                    logger.error("G2B API %s page %d failed: %s", operation, page_no, e)
                    break

    return results


async def _parse_playwright_row(row) -> dict | None:
    try:
        cells = await row.query_selector_all("td")
        if len(cells) < 5:
            return None
        texts = [await c.inner_text() for c in cells]
        link_el = await cells[1].query_selector("a") if len(cells) > 1 else None
        href = await link_el.get_attribute("href") if link_el else None

        raw_budget = texts[4].strip().replace(",", "").replace("원", "") if len(texts) > 4 else ""
        try:
            budget = float(raw_budget) if raw_budget and raw_budget.isdigit() else None
        except ValueError:
            budget = None

        deadline_str = texts[5].strip() if len(texts) > 5 else ""
        try:
            deadline = datetime.strptime(deadline_str[:16], "%Y/%m/%d %H:%M")
        except ValueError:
            deadline = None

        title = texts[1].strip() if len(texts) > 1 else ""
        org = texts[2].strip() if len(texts) > 2 else ""
        bid_num = texts[0].strip() if texts else ""

        if not title or not bid_num:
            return None

        return {
            "bid_number": bid_num,
            "title": title,
            "organization": org,
            "category": texts[3].strip() if len(texts) > 3 else None,
            "budget": budget,
            "deadline": deadline,
            "published_at": datetime.utcnow(),
            "source_url": f"https://www.g2b.go.kr{href}" if href else None,
            "source": "g2b",
            "raw_data": {"cells": texts},
        }
    except Exception as e:
        logger.warning("Row parse failed: %s", e)
        return None


async def _crawl_via_playwright(max_pages: int) -> list[dict]:
    """Playwright 웹 스크래핑 방식 (API 실패 시 폴백)"""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=_UA,
            viewport={"width": 1280, "height": 800},
            locale="ko-KR",
            timezone_id="Asia/Seoul",
        )
        try:
            page: Page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )
            await page.goto(_G2B_LIST_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)

            for page_num in range(1, max_pages + 1):
                rows = []
                for sel in ["table.list tbody tr", "tbody tr", ".tbl_list tbody tr", "table tbody tr"]:
                    rows = await page.query_selector_all(sel)
                    if rows:
                        break

                for row in rows:
                    item = await _parse_playwright_row(row)
                    if item:
                        results.append(item)

                next_btn = await page.query_selector(
                    f"a[onclick*='pageMove({page_num + 1})'], "
                    f"a[onclick*='fn_page({page_num + 1})'], "
                    f".paging a:has-text('{page_num + 1}')"
                )
                if not next_btn:
                    break
                await next_btn.click()
                await page.wait_for_load_state("networkidle", timeout=10000)

        except Exception as e:
            logger.error("Playwright crawl failed: %s", e)
        finally:
            await browser.close()

    return results


async def crawl_g2b(max_pages: int = 5) -> list[dict]:
    if settings.G2B_API_KEY:
        logger.info("G2B crawl via OpenAPI")
        results = await _crawl_via_api(max_pages)
        if results:
            logger.info("g2b crawl done: %d items (API)", len(results))
            return results
        logger.warning("API returned 0 items, falling back to Playwright")

    logger.info("G2B crawl via Playwright")
    results = await _crawl_via_playwright(max_pages)
    logger.info("g2b crawl done: %d items (Playwright)", len(results))
    return results
