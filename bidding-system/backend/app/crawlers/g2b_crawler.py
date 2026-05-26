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
            return datetime.strptime(s[: len(fmt)], fmt)
        except ValueError:
            continue
    return None


def _parse_api_item(item: dict) -> dict | None:
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
        return {
            "bid_number": bid_number,
            "title": item.get("bidNtceNm", "").strip(),
            "organization": item.get("dminsttNm", "").strip(),
            "category": item.get("bidMethdNm") or item.get("ntceInsttOfclNm"),
            "budget": budget,
            "deadline": _parse_dt(item.get("bidClseDt") or item.get("opengDt")),
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
                        parsed = _parse_api_item(raw)
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
