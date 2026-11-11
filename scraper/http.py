"""HTTP-клиент: повторы при сбоях, таймауты и пауза между запросами, чтобы не нагружать сайт."""

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; price-scraper/1.0; portfolio project)"


class HttpClient:
    def __init__(self, delay: float = 0.5, timeout: float = 15, retries: int = 3) -> None:
        self.delay = delay
        self.timeout = timeout
        self._last_request = 0.0
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        retry = Retry(
            total=retries,
            backoff_factor=1,  # 1 с, 2 с, 4 с…
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def get(self, url: str) -> str:
        wait = self.delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        log.debug("GET %s", url)
        response = self.session.get(url, timeout=self.timeout)
        self._last_request = time.monotonic()
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text
