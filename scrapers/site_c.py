"""사이트 C: 차세대반도체컨소시엄 공지사항 — Phase 0 실측 완료.

목록: GET 정적 HTML, JS 렌더링 아님. 데이터 서버에서 완성된 채로 옴.
페이징은 offset 쿼리(10 단위). 상세/등록일 전부 HTML에 그대로 있음.
게시판 특성상 신청기간 같은 구조화된 필드가 없어서 apply_start/deadline은 None 고정.
"""
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

LIST_URL = "https://ngscc.kr/sub/sub04_01.php"
CATEGORY = "차세대반도체 컨소시엄(공통)"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
IDX_RE = re.compile(r"[?&]idx=(\d+)")
PAGE_SIZE = 10
MAX_PAGES = 3  # 하루 두 번 도니까 신규가 이보다 많이 쌓일 일은 거의 없음


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for row in soup.select(".board-list table tbody tr"):
        a = row.select_one("td.subject a")
        if not a or not a.get("href"):
            continue
        m = IDX_RE.search(a["href"])
        if not m:
            continue
        tds = row.find_all("td")
        posted_at = tds[3].get_text(strip=True) if len(tds) > 3 else None
        items.append({
            "id": m.group(1),
            "title": a.get_text(strip=True),
            "url": urljoin(LIST_URL, a["href"]),
            "posted_at": posted_at or None,
            "apply_start": None,
            "deadline": None,
        })
    return items


def fetch():
    result, seen_ids = [], set()
    for page in range(MAX_PAGES):
        params = {"category": CATEGORY, "boardid": "notice", "offset": page * PAGE_SIZE}
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
