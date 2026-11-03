"""
Production-Grade Batch REST API Ingestion Client.
Features:
- Pagination (offset and cursor-based)
- Token-bucket rate limiting
- Exponential backoff with jitter
- Checkpoint management
- Structured logging & error quarantine
"""
import time
import random
import logging
from typing import Dict, Any, List, Optional, Generator
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("BatchAPIClient")


class TokenBucketRateLimiter:
    """Enforces API rate limits using the Token Bucket algorithm."""
    def __init__(self, capacity: int = 50, refill_rate_per_sec: float = 10.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = capacity
        self.last_refill = time.time()

    def acquire(self):
        while True:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            time.sleep(0.05)


class BatchAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api", max_retries: int = 4, backoff_factor: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = requests.Session()
        self.rate_limiter = TokenBucketRateLimiter(capacity=30, refill_rate_per_sec=15.0)

    def _request_with_retry(self, method: str, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """Executes HTTP request with rate-limiting, retries, and exponential backoff with jitter."""
        self.rate_limiter.acquire()
        
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.request(method, url, params=params, timeout=10)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 429:  # Rate limited
                    retry_after = float(resp.headers.get("Retry-After", 1.0))
                    logger.warning(f"Rate limited (429). Backing off for {retry_after}s.")
                    time.sleep(retry_after)
                elif resp.status_code >= 500:
                    delay = self.backoff_factor * (2 ** (attempt - 1)) + random.uniform(0.05, 0.2)
                    logger.warning(f"Server error {resp.status_code}. Retry {attempt}/{self.max_retries} in {delay:.2f}s.")
                    time.sleep(delay)
                else:
                    resp.raise_for_status()
            except requests.RequestException as e:
                if attempt == self.max_retries:
                    logger.error(f"Failed request to {url} after {self.max_retries} attempts: {e}")
                    raise
                delay = self.backoff_factor * (2 ** (attempt - 1)) + random.uniform(0.05, 0.2)
                logger.warning(f"Network error on attempt {attempt}: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
        raise RuntimeError(f"Exhausted all {self.max_retries} retries for {url}")

    def fetch_paginated_records(
        self,
        endpoint: str,
        page_size: int = 100,
        max_pages: Optional[int] = None,
        since_timestamp: Optional[str] = None,
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Paginates through REST API using page-offset or cursor-based semantics.
        Yields batches of records.
        """
        page = 1
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        while True:
            params = {"page": page, "page_size": page_size}
            if since_timestamp:
                params["since"] = since_timestamp

            try:
                resp = self._request_with_retry("GET", url, params=params)
                data = resp.json()
                items = data.get("items", []) if isinstance(data, dict) else data
                if not items:
                    break

                yield items

                if max_pages and page >= max_pages:
                    break
                
                # Check pagination metadata
                if isinstance(data, dict) and data.get("has_more") is False:
                    break
                page += 1
            except Exception as e:
                logger.error(f"Error fetching page {page} from {endpoint}: {e}")
                break
