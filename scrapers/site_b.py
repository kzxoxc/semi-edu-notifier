"""사이트 B: 반도체인프라활용현장인력양성 — Phase 0 실측 완료.

주의: 이 사이트 robots.txt는 이 목록 경로(/user/Wo/WoUser0101.do)를 Disallow 한다.
사용자가 직접 "robots.txt 무시하고 수집" 지시해서 진행함 (2026-08-14 대화 기록).

목록: GET 정적 HTML, JS 렌더링 아님. 페이징은 CURR_PAGE 쿼리로 됨 (VIEW_SIZE=10 고정).
상세페이지(WoUser0101V.do)는 POST 전용이라 세션 쿠키+전체 hidden form 필드 없인
무조건 /main.do로 302 리다이렉트됨 — 텔레그램에 넣을 단순 GET 링크가 없다.
그래서 링크는 목록 페이지 URL로 대체한다 (알려진 한계, README에도 기재).
"""
import re
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

LIST_URL = "https://infra.ksia.or.kr/user/Wo/WoUser0101.do"
LIST_PARAMS = {
    "SCH_PRM_GB": "002",
    "TAB_ID": "1",
    "CURRENT_MENU_CODE": "MENU0040",
    "TOP_MENU_CODE": "MENU0040",
}
LIST_LINK = f"{LIST_URL}?{urlencode(LIST_PARAMS)}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
SEQ_RE = re.compile(r"fnMoveView\('(\d+)'")
VIEW_SIZE = 10
MAX_PAGES = 3  # 하루 두 번 도니까 신규가 이보다 많이 쌓일 일은 거의 없음


def _dot_to_dash(s):
    s = (s or "").strip()
    return s.replace(".", "-") if s else None


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("ul.programList li"):
        a = li.select_one(".title a")
        if not a:
            continue
        m = SEQ_RE.search(a.get("onclick", ""))
        if not m:
            continue
        seq = m.group(1)
        title = a.get_text(strip=True)

        apply_start = apply_end = None
        for p in li.select(".date p"):
            dfn, span = p.find("dfn"), p.find("span")
            if dfn and span and "모집기간" in dfn.get_text():
                parts = span.get_text(strip=True).split("~")
                if len(parts) == 2:
                    apply_start = _dot_to_dash(parts[0])
                    apply_end = _dot_to_dash(parts[1])

        items.append({
            "id": seq,
            "title": title,
            "url": LIST_LINK,
            "posted_at": apply_start,
            "apply_start": apply_start,
            "deadline": apply_end,
        })
    return items


def fetch():
    result, seen_ids = [], set()
    for page in range(1, MAX_PAGES + 1):
        params = dict(LIST_PARAMS, CURR_PAGE=page)
        resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        page_items = _parse_page(resp.text)
        if not page_items:
            break
        for it in page_items:
            if it["id"] not in seen_ids:
                seen_ids.add(it["id"])
                result.append(it)
        if len(page_items) < VIEW_SIZE:
            break
    return result
