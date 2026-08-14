"""사이트 A: 한국반도체아카데미 (오프라인 강의) — Phase 0 실측 완료.

목록 API: POST https://academy.ksia.or.kr/dclassapi/lecture/u/retrieveAllPaging
- lectGb "02" = 오프라인, "01" = 온라인. 로그인/쿠키 불필요 (공개 엔드포인트).
- 관리자용 /lecture/a/retrieveAllPaging 은 별개 (401) — 이건 쓰면 안 됨.
- lectTrgt: "COMPANY"(재직자) / "STUDENT"(학생) / "ALL"(전체) 로 실측 확인됨.
  사용자 요청: 재직자(COMPANY) 대상 교육은 제외. 새 값이 나오면(모르는 값) 판단 못하니
  일단 포함해서 알린다 — 조용히 누락시키는 게 더 위험하다.
- regDt(등록일시)는 실측 샘플 전부 null이라 못 씀. createDate를 posted_at으로 쓴다.
"""
import requests

API_URL = "https://academy.ksia.or.kr/dclassapi/lecture/u/retrieveAllPaging"
DETAIL_URL = "https://academy.ksia.or.kr/lecture/offline/detail/{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json; charset=UTF-8",
}
EXCLUDED_TARGETS = {"COMPANY"}  # 재직자 대상 — 요청에 따라 제외


def _ymd(s):
    # "20260813" -> "2026-08-13". 빈 값/None 이면 그대로 None.
    if not s or len(s) != 8:
        return None
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def fetch():
    resp = requests.post(
        API_URL,
        headers=HEADERS,
        json={
            "lectGb": "02",
            "lectOpenYn": "Y",
            "searchDurationGb": "C",
            "regTermYn": "",
            "pageNumber": 1,
            "size": 50,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    items = data["result"]["content"]

    result = []
    for it in items:
        if it.get("lectTrgt") in EXCLUDED_TARGETS:
            continue
        lect_id = it["lectId"]
        posted_at = (it.get("createDate") or "")[:10] or None
        result.append({
            "id": str(lect_id),
            "title": it.get("lectName", ""),
            "url": DETAIL_URL.format(lect_id),
            "posted_at": posted_at,
            "apply_start": _ymd(it.get("regStartYmd")),
            "deadline": _ymd(it.get("regEndYmd")),
            # 교육기간 (며칠짜리인지) — 자동 필터링은 안 하고 메시지에만 표시.
            # 캘린더 일수만으로 장/단기 자동 판단하면 "주 1회 X주" 같은 과정을
            # 잘못 걸러낼 수 있어서 사람이 보고 판단하게 둠.
            "period_start": _ymd(it.get("lectStartYmd")),
            "period_end": _ymd(it.get("lectEndYmd")),
        })
    return result
