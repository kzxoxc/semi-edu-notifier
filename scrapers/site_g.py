"""사이트 G: 서울대 반도체공동연구소(ISRC) 정기교육 접수신청.

목록: 화면은 JS 렌더링이지만 데이터 자체는 JSON API로 바로 옴 (JSESSIONID 쿠키 불필요).
페이징은 page/rows 쿼리. 접수기간이 구조화된 필드로 오므로 apply_start/deadline 채움.
"""
import requests

LIST_URL = "https://isrc.snu.ac.kr/edu/school/event/gen/list/json"
DETAIL_URL = "https://isrc.snu.ac.kr/edu/school/event/detail"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}
PAGE_SIZE = 20
MAX_PAGES = 3  # 하루 두 번 도니까 신규가 이보다 많이 쌓일 일은 거의 없음


def _parse_page(data):
    items = []
    for row in data.get("rows", []):
        key = row.get("EVENT_SKEY")
        if key is None:
            continue
        items.append({
            "id": str(key),
            "title": row.get("NAME", ""),
            "url": f"{DETAIL_URL}?EVENT_SKEY={key}",
            "posted_at": None,
            "apply_start": row.get("RECEIVE_START_DT_STR"),
            "deadline": row.get("RECEIVE_END_DT_STR"),
        })
    return items


def fetch():
    result, seen_ids = [], set()
    for page in range(1, MAX_PAGES + 1):
        params = {
            "page": page,
            "rows": PAGE_SIZE,
            "TYPE_LIST": "",
            "EVENT_SUB_TYPE": "RG",
            "USER_VIEW": "Y",
            "STATUS": "A",
            "HEADER": "",
            "searchKey": "",
            "searchValue": "",
            "EVENT_TYPE": "EDU01",
        }
        resp = requests.post(LIST_URL, data=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        page_items = _parse_page(resp.json())
        if not page_items:
            break
        for it in page_items:
            if it["id"] not in seen_ids:
                seen_ids.add(it["id"])
                result.append(it)
        if len(page_items) < PAGE_SIZE:
            break
    return result
