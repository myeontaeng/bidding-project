"""나라장터(g2b.go.kr) 입찰 공고 크롤러"""
import logging
from datetime import datetime
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)

G2B_BID_URL = "https://www.g2b.go.kr/pt/menu/selectSubFrame.do?framesrc=/pt/menu/frameTgong.do?searchType=bidPbancList"


async def _parse_row(row) -> dict | None:
    try:
        cells = await row.query_selector_all("td")
        if len(cells) < 6:
            return None

        texts = [await c.inner_text() for c in cells]

        link_el = await cells[1].query_selector("a")
        url = await link_el.get_attribute("href") if link_el else None

        raw_budget = texts[4].strip().replace(",", "").replace("원", "")
        try:
            budget = float(raw_budget) if raw_budget else None
        except ValueError:
            budget = None

        deadline_str = texts[5].strip()
        try:
            deadline = datetime.strptime(deadline_str[:16], "%Y/%m/%d %H:%M")
        except ValueError:
            deadline = None

        return {
            "bid_number": texts[0].strip(),
            "title": texts[1].strip(),
            "organization": texts[2].strip(),
            "category": texts[3].strip() or None,
            "budget": budget,
            "deadline": deadline,
            "source_url": f"https://www.g2b.go.kr{url}" if url else None,
            "source": "g2b",
            "published_at": datetime.utcnow(),
            "raw_data": {"cells": texts},
        }
    except Exception as e:
        logger.warning("Row parse failed: %s", e)
        return None


async def crawl_g2b(max_pages: int = 5) -> list[dict]:
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page: Page = await browser.new_page()
            await page.goto(G2B_BID_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)

            for page_num in range(1, max_pages + 1):
                try:
                    rows = await page.query_selector_all("table.list tbody tr")
                    for row in rows:
                        item = await _parse_row(row)
                        if item:
                            results.append(item)

                    next_btn = await page.query_selector(f"a[onclick*='pageMove({page_num + 1})']")
                    if not next_btn:
                        break
                    await next_btn.click()
                    await page.wait_for_load_state("networkidle", timeout=10000)

                except Exception as e:
                    logger.error("Page %d crawl failed: %s", page_num, e)
                    break

        finally:
            await browser.close()

    logger.info("g2b crawl done: %d items", len(results))
    return results
