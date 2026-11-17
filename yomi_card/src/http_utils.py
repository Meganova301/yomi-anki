import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Optional, Union

import requests


_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def _retry_after_seconds(value: Optional[str]) -> Optional[Union[int, float]]:
    if value is None:
        return None

    try:
        delay = int(value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)

        delay = (retry_at - datetime.now(timezone.utc)).total_seconds()
        if delay < 0:
            return 0.0
    else:
        if delay < 0:
            return None

    return delay


def request_with_retries(
    request: Callable[..., requests.Response],
    *args: Any,
    retry_safe: bool,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    max_retry_after: float = 30.0,
    **kwargs: Any,
) -> requests.Response:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")
    if base_delay < 0 or max_delay < 0 or max_retry_after < 0:
        raise ValueError("Retry delays cannot be negative.")

    attempt = 0
    while True:
        attempt += 1
        response: Optional[requests.Response] = None
        retry_after: Optional[Union[int, float]] = None

        try:
            response = request(*args, **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if not retry_safe or attempt >= max_attempts:
                raise
        else:
            is_retryable_status = (
                response.status_code in _RETRYABLE_STATUS_CODES
            )
            if not retry_safe or not is_retryable_status:
                response.raise_for_status()
                return response

            retry_after = _retry_after_seconds(
                response.headers.get("Retry-After")
            )

            if retry_after is not None and retry_after > max_retry_after:
                response.raise_for_status()
                raise requests.HTTPError(
                    f"Retry-After exceeds the {max_retry_after:g}s wait limit.",
                    response=response,
                )

            if attempt >= max_attempts:
                response.raise_for_status()
                raise requests.HTTPError(
                    f"HTTP {response.status_code} after {attempt} attempts.",
                    response=response,
                )

        fallback_delay = min(
            base_delay * (2 ** (attempt - 1)),
            max_delay,
        )
        delay = fallback_delay if retry_after is None else retry_after

        if delay:
            time.sleep(delay)