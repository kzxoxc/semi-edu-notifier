import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def retry_session():
    """연결 실패/5xx 시 최대 3회 재시도 (대기 2s, 4s, 8s). GitHub 러너→국내 서버 일시 타임아웃 대응."""
    s = requests.Session()
    retry = Retry(total=3, connect=3, read=2, status=2, backoff_factor=2,
                  status_forcelist=(502, 503, 504), allowed_methods=("GET",))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s
