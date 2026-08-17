"""사이트 D: 인하대 학생진로설계포털 취업프로그램 전체목록 — Phase 0 실측 완료.

목록: GET 정적 HTML, JS 렌더링 아님 (ASP.NET UpdatePanel 페이징이지만 쿼리스트링
GET으로도 같은 결과 나옴 — 실측 확인). prodiv 파라미터 생략하면 전체 카테고리
(진로/취업프로그램/채용설명회/졸업생특화 등) 다 나옴 — 사용자가 "전체" 요청.
페이징은 rp 쿼리 (1페이지=rp 생략, 16건/페이지).
등록일 필드가 목록에 없어서 "신청" 기간 시작일을 posted_at으로 대신 씀 (site_b와 동일 패턴).

주의: goView('pgdx') 토큰은 매 요청마다 값이 바뀜 (같은 항목인데도 fetch할 때마다 다른
문자열 — 실측으로 확인. 링크 자체는 예전 토큰도 계속 유효하지만, seen.json 대조용 id로
쓰면 매번 "신규"로 오판해 매 실행마다 전체 재알림 나가버림). 그래서 id는 제목+신청기간을
해시해서 만들고, pgdx는 상세페이지 링크(url)에만 쓴다.
"""
import hashlib
import re

import requests
from bs4 import BeautifulSoup

LIST_URL = "https://job.inha.ac.kr/community/Program/ProgramList.aspx"
DETAIL_URL = "https://job.inha.ac.kr/community/Program/programView.aspx?pgdx={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
TOKEN_RE = re.compile(r"goView\('([^']+)'\)")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})~(\d{4}-\d{2}-\d{2})")
PAGE_SIZE = 16
MAX_PAGES = 3  # 하루 두 번 도니까 신규가 이보다 많이 쌓일 일은 거의 없음


def _parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("li[onclick^='javascript:goView']"):
        m = TOKEN_RE.search(li.get("onclick", ""))
        if not m:
            continue
        token = m.group(1)

        info = li.select_one(".info-box")
        title_el = info.select_one("[id$='_Title_txt']") if info else None
        title = title_el.get_text(strip=True) if title_el else ""

        apply_el = info.select_one("[id$='_DateTime_txt']") if info else None
        apply_start = apply_end = None
        if apply_el:
            dm = DATE_RE.search(apply_el.get_text())
            if dm:
                apply_start, apply_end = dm.group(1), dm.group(2)

        stable_id = hashlib.sha1(f"{title}|{apply_start}|{apply_end}".encode("utf-8")).hexdigest()[:16]
        items.append({
            "id": stable_id,
            "title": title,
            "url": DETAIL_URL.format(token),
            "posted_at": apply_start,
            "apply_start": apply_start,
            "deadline": apply_end,
        })
    return items


def fetch():
    result, seen_ids = [], set()
    for page in range(1, MAX_PAGES + 1):
        params = {} if page == 1 else {"rp": page}
        resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"  # 서버가 헤더에 charset 안 붙여줘서 requests가 오탐지함
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
