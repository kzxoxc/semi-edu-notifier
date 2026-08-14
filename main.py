"""오케스트레이션만. 사이트별 수집 → 신규 판정 → 알림 → seen.json 갱신.
Git 커밋/푸시는 여기서 안 함 — GitHub Actions 워크플로 쪽 책임.
"""
import json
import time
from pathlib import Path

import notify
from scrapers import site_a, site_b, site_c

SEEN_PATH = Path(__file__).parent / "seen.json"
MAX_SEEN = 500

# (표시용 이름, 스크래퍼 모듈, seen.json 안에서 id 충돌 안 나게 붙이는 접두어)
SITES = [
    ("반도체 아카데미", site_a, "A"),
    ("반도체인프라활용현장인력양성", site_b, "B"),
    ("차세대반도체컨소시엄", site_c, "C"),
]


def load_seen():
    if not SEEN_PATH.exists():
        return []
    return json.loads(SEEN_PATH.read_text(encoding="utf-8"))


def save_seen(seen_list):
    trimmed = seen_list[-MAX_SEEN:]
    SEEN_PATH.write_text(json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    seen = load_seen()
    seen_set = set(seen)
    newly_seen = []

    for i, (name, module, prefix) in enumerate(SITES):
        if i > 0:
            time.sleep(1.5)  # 사이트 간 간격 (요구사항 8)

        try:
            items = module.fetch()
        except Exception as e:
            notify.send_error(name, type(e).__name__, str(e))
            continue

        if len(items) == 0:
            notify.send_zero_warning(name)
            continue

        new_items = [it for it in items if f"{prefix}:{it['id']}" not in seen_set]
        if new_items:
            notify.send_new_items(name, new_items)
            for it in new_items:
                key = f"{prefix}:{it['id']}"
                seen_set.add(key)
                newly_seen.append(key)

    if newly_seen:
        save_seen(seen + newly_seen)


if __name__ == "__main__":
    main()
