"""텔레그램 전송만 담당. 토큰/chat_id는 환경변수에서만 읽는다 (하드코딩 금지)."""
import os
from datetime import date

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_LEN = 4096


def _token_and_chat():
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    return token, chat_id


def _send_raw(text):
    token, chat_id = _token_and_chat()
    resp = requests.post(
        TELEGRAM_API.format(token=token),
        data={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=15,
    )
    resp.raise_for_status()


def _send_chunked(lines):
    """줄 단위로 모아서 4096자 넘기 직전에 끊어 보낸다."""
    chunk = ""
    for line in lines:
        candidate = chunk + line + "\n"
        if len(candidate) > MAX_LEN and chunk:
            _send_raw(chunk.rstrip("\n"))
            chunk = line + "\n"
        else:
            chunk = candidate
    if chunk.strip():
        _send_raw(chunk.rstrip("\n"))


def _period_line(it):
    """period_start/period_end 있는 사이트(현재 A만)에서 '교육기간: ~ (n일)' 줄 생성.
    없는 사이트는 None 반환 — 필드 자체가 없는 사이트 메시지엔 이 줄 안 붙는다."""
    start, end = it.get("period_start"), it.get("period_end")
    if not start or not end:
        return None
    try:
        days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    except ValueError:
        return f"  교육기간: {start} ~ {end}"
    return f"  교육기간: {start} ~ {end} ({days}일)"


def send_new_items(site_name, items):
    """신규 공고 알림. items가 비어있으면 아무것도 안 보낸다 (요구사항 6)."""
    if not items:
        return
    lines = [f"🆕 [{site_name}] 신규 {len(items)}건", ""]
    for it in items:
        lines.append(f"• {it['title']}")
        lines.append(f"  신청시작: {it.get('apply_start') or '미기재'}")
        lines.append(f"  마감: {it.get('deadline') or '미기재'}")
        period = _period_line(it)
        if period:
            lines.append(period)
        lines.append(f"  {it['url']}")
        lines.append("")
    _send_chunked(lines)


def send_zero_warning(site_name):
    _send_raw(f"⚠️ [{site_name}] 파싱 결과 0건 — 셀렉터 점검 필요")


def send_error(site_name, error_type, error_message):
    _send_raw(f"❌ [{site_name}] 오류: {error_type} — {error_message}")
