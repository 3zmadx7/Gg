import json
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError, URLError

import pandas as pd


MAX_CANDLES_PER_REQUEST = 5000


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _rfc3339(dt: datetime) -> str:
    dt_utc = _to_utc(dt)
    return dt_utc.isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    if "." in normalized:
        head, tail = normalized.split(".", 1)
        frac, offset = tail[:6], tail[tail.find("+") :] if "+" in tail else ""
        normalized = f"{head}.{frac.ljust(6, '0')}{offset}"
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def _request_json(url: str, token: str, params: dict[str, Any]) -> dict[str, Any]:
    query = parse.urlencode(params)
    req = request.Request(
        f"{url}?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OANDA HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"OANDA request failed: {exc}") from exc


def download_oanda_candles(
    instrument: str,
    granularity: str,
    from_dt: datetime,
    to_dt: datetime,
) -> pd.DataFrame:
    """Download complete OANDA midpoint candles as OHLCV rows.

    Returns columns: time (tz-naive UTC), open, high, low, close, volume.
    Automatically paginates across OANDA's 5000-candle response limit.
    """
    token = os.environ.get("OANDA_TOKEN")
    base_url = os.environ.get("OANDA_BASE_URL", "https://api-fxpractice.oanda.com/v3").rstrip("/")
    if not token:
        raise RuntimeError("OANDA_TOKEN is not set")

    endpoint = f"{base_url}/instruments/{instrument}/candles"
    cursor = _to_utc(from_dt)
    end = _to_utc(to_dt)
    rows: list[dict[str, Any]] = []
    seen_times: set[str] = set()

    while cursor < end:
        params = {
            "granularity": granularity,
            "from": _rfc3339(cursor),
            "price": "M",
            "count": MAX_CANDLES_PER_REQUEST,
        }

        data = None
        last_error = None
        for attempt in range(2):
            try:
                data = _request_json(endpoint, token, params)
                break
            except RuntimeError as exc:
                last_error = exc
                if attempt == 0:
                    time.sleep(2)
        if data is None:
            raise last_error or RuntimeError("OANDA request failed")

        candles = data.get("candles", [])
        complete = [c for c in candles if c.get("complete") and "mid" in c]
        if not complete:
            break

        for candle in complete:
            parsed_time = _parse_time(candle["time"])
            if parsed_time > end:
                continue
            t = candle["time"]
            if t in seen_times:
                continue
            seen_times.add(t)
            mid = candle["mid"]
            rows.append(
                {
                    "time": parsed_time.replace(tzinfo=None),
                    "open": float(mid["o"]),
                    "high": float(mid["h"]),
                    "low": float(mid["l"]),
                    "close": float(mid["c"]),
                    "volume": int(candle.get("volume", 0)),
                }
            )

        last_time = _parse_time(complete[-1]["time"])
        if last_time >= end:
            break
        next_cursor = last_time + timedelta(microseconds=1)
        if next_cursor <= cursor:
            break
        cursor = next_cursor

    df = pd.DataFrame(rows, columns=["time", "open", "high", "low", "close", "volume"])
    if df.empty:
        return df
    df.sort_values("time", inplace=True)
    df.drop_duplicates(subset=["time"], keep="last", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
