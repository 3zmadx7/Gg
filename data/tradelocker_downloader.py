import os
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, Dict, List

TRADELOCKER_ENV    = os.environ.get("TRADELOCKER_ENV",    "https://demo.tradelocker.com")
TRADELOCKER_USER   = os.environ.get("TRADELOCKER_USER",   "azma.dx7@gmail.com")
TRADELOCKER_PASS   = os.environ.get("TRADELOCKER_PASS",   "20cA'}")
TRADELOCKER_SERVER = os.environ.get("TRADELOCKER_SERVER", "AQUA")

_RESOLUTION_MAP = {1: "1m", 5: "5m", 15: "15m", 30: "30m", 60: "1H", 240: "4H"}
MAX_BARS_PER_CALL = 5000


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("tradelocker_downloader")
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(h)
    logger.setLevel(logging.INFO)
    return logger


class TradeLockerDownloader:
    def __init__(self):
        self.logger       = _setup_logger()
        self.session      = requests.Session()
        self.access_token: Optional[str] = None
        self.account_id:   Optional[int] = None
        self.acc_num:      Optional[int] = None
        self.symbol_map:   Dict[str, Dict] = {}

    def authenticate(self) -> bool:
        url = f"{TRADELOCKER_ENV}/backend-api/auth/jwt/token"
        payload = {
            "email":    TRADELOCKER_USER,
            "password": TRADELOCKER_PASS,
            "server":   TRADELOCKER_SERVER,
        }
        try:
            r = self.session.post(url, json=payload, timeout=20)
            if r.status_code not in (200, 201):
                self.logger.error(f"Auth failed {r.status_code}: {r.text[:300]}")
                return False
            self.access_token = r.json().get("accessToken")
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

            acc_r = self.session.get(
                f"{TRADELOCKER_ENV}/backend-api/auth/jwt/all-accounts", timeout=20
            )
            if acc_r.status_code != 200:
                self.logger.error(f"Accounts fetch failed {acc_r.status_code}")
                return False
            accounts = acc_r.json().get("accounts", [])
            if not accounts:
                self.logger.error("No accounts found")
                return False
            acc = accounts[0]
            self.account_id = acc.get("id")
            self.acc_num    = acc.get("accNum")
            self.session.headers.update({"accNum": str(self.acc_num)})
            self._load_instruments()
            self.logger.info(f"Authenticated | Account #{self.acc_num} | id={self.account_id}")
            return True
        except Exception as e:
            self.logger.error(f"Auth exception: {e}")
            return False

    def _load_instruments(self) -> None:
        try:
            url = f"{TRADELOCKER_ENV}/backend-api/trade/accounts/{self.account_id}/instruments"
            r = self.session.get(url, timeout=20)
            if r.status_code != 200:
                self.logger.warning(f"Instruments {r.status_code}")
                return
            instruments = r.json().get("d", {}).get("instruments", [])
            self.symbol_map = {}
            for inst in instruments:
                key = inst.get("name", "").replace("/", "").upper()
                self.symbol_map[key] = inst
            self.logger.info(f"Loaded {len(self.symbol_map)} instruments")
        except Exception as e:
            self.logger.warning(f"Instrument load: {e}")

    def find_instrument(self, symbol: str) -> Optional[Dict]:
        sym = symbol.replace("/", "").upper()
        inst = self.symbol_map.get(sym)
        if inst:
            return inst
        base = sym.split(".")[0]
        inst = self.symbol_map.get(base)
        if inst:
            return inst
        for key, value in self.symbol_map.items():
            if key.split(".")[0] == base or key == f"{base}.R":
                return value
        return None

    def _info_route_id(self, inst: Dict) -> Optional[int]:
        for rt in inst.get("routes", []):
            if rt.get("type") == "INFO":
                return rt.get("id")
        routes = inst.get("routes", [])
        return routes[0].get("id") if routes else None

    def _dt_to_ms(self, dt: datetime) -> int:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    def get_candles_range(
        self,
        symbol: str,
        resolution_minutes: int,
        from_dt: datetime,
        to_dt: datetime,
    ) -> Optional[pd.DataFrame]:
        inst = self.find_instrument(symbol)
        if not inst:
            self.logger.error(f"Instrument not found: {symbol}")
            self.logger.info(f"Available symbols: {list(self.symbol_map.keys())[:20]}")
            return None

        resolution_str = _RESOLUTION_MAP.get(resolution_minutes)
        if not resolution_str:
            self.logger.error(f"Unsupported resolution: {resolution_minutes}")
            return None

        route_id = self._info_route_id(inst)
        tid      = inst.get("tradableInstrumentId")
        url      = f"{TRADELOCKER_ENV}/backend-api/trade/history"

        from_ms  = self._dt_to_ms(from_dt)
        to_ms    = self._dt_to_ms(to_dt)
        step_ms  = MAX_BARS_PER_CALL * resolution_minutes * 60 * 1000

        all_bars: List[dict] = []
        cursor   = from_ms

        self.logger.info(
            f"Downloading {symbol} {resolution_minutes}m | "
            f"{from_dt.date()} → {to_dt.date()}"
        )

        while cursor < to_ms:
            chunk_to = min(cursor + step_ms, to_ms)
            params = {
                "routeId":               route_id,
                "tradableInstrumentId":  tid,
                "resolution":            resolution_str,
                "from":                  cursor,
                "to":                    chunk_to,
            }
            retry_delay = 5
            chunk_ok = False
            for attempt in range(6):
                try:
                    r = self.session.get(url, params=params, timeout=30)
                    if r.status_code == 401:
                        self.logger.warning("Token expired, re-authenticating...")
                        self.authenticate()
                        r = self.session.get(url, params=params, timeout=30)

                    if r.status_code == 429:
                        self.logger.warning(f"Rate-limited (429) — sleeping {retry_delay}s then retrying chunk...")
                        time.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 60)
                        continue

                    if r.status_code != 200:
                        self.logger.warning(f"Candles HTTP {r.status_code}: {r.text[:200]}")
                        break

                    j = r.json()
                    if j.get("s") != "ok":
                        self.logger.warning(f"API s={j.get('s')} errmsg={j.get('errmsg')}")
                        break

                    d = j.get("d", {})
                    bars = d.get("barDetails", []) if isinstance(d, dict) else []
                    if bars:
                        all_bars.extend(bars)
                        self.logger.info(
                            f"  Chunk {len(all_bars)} bars so far | "
                            f"{datetime.fromtimestamp(cursor/1000, tz=timezone.utc).date()} → "
                            f"{datetime.fromtimestamp(chunk_to/1000, tz=timezone.utc).date()}"
                        )
                    else:
                        self.logger.info(f"  Empty chunk {datetime.fromtimestamp(cursor/1000, tz=timezone.utc).date()}")
                    chunk_ok = True
                    break

                except Exception as e:
                    self.logger.warning(f"Chunk error (attempt {attempt+1}): {e}")
                    time.sleep(2)

            cursor = chunk_to
            time.sleep(0.5)

        if not all_bars:
            self.logger.error(f"No bars returned for {symbol}")
            return None

        df = pd.DataFrame(all_bars)
        rename = {"o": "open", "h": "high", "l": "low", "c": "close", "v": "volume", "t": "time_ms"}
        df.rename(columns={k: v for k, v in rename.items() if k in df.columns}, inplace=True)

        for col in ["open", "high", "low", "close", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "time_ms" in df.columns:
            df["time"] = pd.to_datetime(df["time_ms"], unit="ms", utc=True).dt.tz_localize(None)

        df = df.dropna(subset=["close"]).drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
        self.logger.info(f"Done: {len(df)} bars for {symbol} {resolution_minutes}m")
        return df


def download_m1(
    symbol: str,
    from_dt: datetime,
    to_dt: datetime,
) -> Optional[pd.DataFrame]:
    dl = TradeLockerDownloader()
    if not dl.authenticate():
        return None
    return dl.get_candles_range(symbol, 1, from_dt, to_dt)


if __name__ == "__main__":
    dl = TradeLockerDownloader()
    ok = dl.authenticate()
    print(f"Auth: {ok}")
    if ok:
        print(f"Account ID : {dl.account_id}")
        print(f"Account Num: {dl.acc_num}")
        print(f"Instruments: {len(dl.symbol_map)}")
        print("Sample symbols:", list(dl.symbol_map.keys())[:30])
