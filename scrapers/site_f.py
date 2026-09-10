"""사이트 F: 나노종합기술원(NNFC) 교육일정 및 신청.

주의: 이 사이트 robots.txt는 전체 경로(Disallow: /)를 막고 있는데, 사용자가 site_b와
동일하게 "무시하고 수집" 지시해서 진행함 (2026-09-10 대화 기록).

목록: GET 정적 HTML, JS 렌더링 아님 (연간 전체 일정이 한 페이지에 다 옴, 페이징 없음).
상세보기(button_view)는 onclick JS로 모달 띄우는 방식이라 단순 GET 링크가 없다 —
site_b와 동일한 한계라 링크는 목록 페이지 URL로 대체한다.
"""
import re

import requests
from bs4 import BeautifulSoup

LIST_URL = "https://www.nnfc.re.kr/prog/edu/kor/sub01_03_04_02/list_year.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
# "2026-01-01 00:00", "2026.03.16", "2026. 06.19" (점 뒤 띄어쓰기 섞인 경우까지) 다 잡는다.
DATE_RE = re.compile(r"(\d{4})[.\-]\s?(\d{1,2})[.\-]\s?(\d{1,2})")


def _dates_in(text):
    """텍스트 안 날짜 토큰들을 ["YYYY-MM-DD", ...] 순서대로 뽑는다 (시각 등 뒷부분은 버림)."""
    return [f"{y}-{m.zfill(2)}-{d.zfill(2)}" for y, m, d in DATE_RE.findall(text)]


def fetch():
    resp = requests.get(LIST_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    result = []
    for tr in soup.select("tbody tr"):
        view = tr.select_one("a.button_view[data-key-no]")
        if not view:
            continue
        key_no = view["data-key-no"]
        # 열 순서 고정: [0]제목 [1]대상 [2]모집기간 [3]교육기간 (뒤는 상태/버튼 — 개수 안 바뀜)
        tds = tr.find_all("td")
        title = tds[0].get_text(strip=True) if tds else ""

        apply_dates = _dates_in(tds[2].get_text()) if len(tds) > 2 else []
        period_dates = _dates_in(tds[3].get_text()) if len(tds) > 3 else []
        apply_start = apply_dates[0] if len(apply_dates) > 0 else None
        apply_end = apply_dates[1] if len(apply_dates) > 1 else None
        period_start = period_dates[0] if len(period_dates) > 0 else None
        period_end = period_dates[1] if len(period_dates) > 1 else period_start

        result.append({
            "id": key_no,
            "title": title,
            "url": LIST_URL,
            "posted_at": apply_start,
            "apply_start": apply_start,
            "deadline": apply_end,
            "period_start": period_start,
            "period_end": period_end,
        })
    return result
