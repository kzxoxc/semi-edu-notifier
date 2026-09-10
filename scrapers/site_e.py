"""사이트 E: 한국반도체교육원(KSTI) 교육프로그램 신청.

목록: GET 정적 HTML, JS 렌더링 아님. 페이징은 page 쿼리 (8건/페이지).
신청기간이 구조화된 데이터로 안 오고 "접수중"/"접수마감 D-7"/"접수마감되었습니다" 같은
상태 문구만 있어서 site_c처럼 apply_start/deadline은 못 채운다 — 대신 상태 문구를
deadline 필드에 그대로 넣어서 알림에 보이게 한다.
"""
import re

import requests
from bs4 import BeautifulSoup

LIST_URL = "https://ksti.co.kr/bbs/board.php"
LIST_PARAMS = {"bo_table": "reqclass"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
RM_IX_RE = re.compile(r"rm_ix=(\d+)")
PAGE_SIZE = 8
MAX_PAGES = 3  # 하루 두 번 도니까 신규가 이보다 많이 쌓일 일은 거의 없음


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("#class_list > li"):
        a = li.select_one(".title") and li.select_one("a[href*='rm_ix=']")
        if not a:
            continue
        m = RM_IX_RE.search(a["href"])
        if not m:
            continue
        title_el = li.select_one(".title")
        date_el = li.select_one(".date")
        items.append({
            "id": m.group(1),
            "title": title_el.get_text(strip=True) if title_el else "",
            "url": a["href"],
            "posted_at": None,
            "apply_start": None,
            "deadline": date_el.get_text(strip=True) if date_el else None,
        })
    return items


def fetch():
    result, seen_ids = [], set()
    for page in range(1, MAX_PAGES + 1):
        params = dict(LIST_PARAMS) if page == 1 else dict(LIST_PARAMS, page=page)
        resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        page_items = _parse_page(resp.text)
        if not page_items:
            break
        for it in page_items:
            if it["id"] not in seen_ids:
                seen_ids.add(it["id"])
                result.append(it)
        if len(page_items) < PAGE_SIZE:
            break
    return result
