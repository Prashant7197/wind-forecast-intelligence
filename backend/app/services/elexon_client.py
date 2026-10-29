import hashlib, json, os, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import httpx

class ElexonDataError(RuntimeError):
    pass

def parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

class ElexonClient:
    # Keep API parameters here so changes in Elexon's API can be applied in one place.
    def __init__(self):
        self.base = os.getenv("ELEXON_API_BASE", "https://data.elexon.co.uk/bmrs/api/v1").rstrip("/")
        self.cache_dir = Path(os.getenv("CACHE_DIR", "data/cache"))
        self.cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "1800"))
        self.timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, url: str, params: dict[str, Any]):
        key = hashlib.sha256((url + json.dumps(params, sort_keys=True, default=str)).encode()).hexdigest()
        return self.cache_dir / f"{key}.json"

    @staticmethod
    def _records(payload: Any):
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]
        if isinstance(payload, dict):
            for key in ("data", "results", "records", "items"):
                if isinstance(payload.get(key), list):
                    return [r for r in payload[key] if isinstance(r, dict)]
        raise ElexonDataError("Unexpected response format; expected a JSON array or a wrapper containing an array.")

    async def _get(self, dataset: str, params: dict, refresh=False):
        url = f"{self.base}/datasets/{dataset}/stream"
        path = self._path(url, params)
        if path.exists() and not refresh and time.time() - path.stat().st_mtime < self.cache_ttl:
            try:
                return self._records(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as session:
                response = await session.get(url, params=params, headers={"Accept": "application/json"})
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ElexonDataError(f"{dataset} API request failed: {exc}") from exc
        rows = self._records(payload)
        try:
            path.write_text(json.dumps(rows), encoding="utf-8")
        except OSError:
            pass
        return rows

    async def fetch_actuals(self, start: datetime, end: datetime, refresh=False):
        params = {"settlementDateFrom": start.date().isoformat(), "settlementDateTo": end.date().isoformat(), "fuelType": "WIND"}
        rows = await self._get("FUELHH", params, refresh)
        result = []
        for row in rows:
            if str(row.get("fuelType", "")).upper() != "WIND" or not row.get("startTime") or row.get("generation") is None:
                continue
            try:
                target = parse_dt(row["startTime"])
            except ValueError:
                continue
            if start <= target < end:
                result.append(row)
        return result

    async def fetch_forecasts(self, target_start: datetime, target_end: datetime, publish_from: datetime, publish_to: datetime, refresh=False):
        params = {
            "settlementDateFrom": target_start.date().isoformat(),
            "settlementDateTo": target_end.date().isoformat(),
            "publishDateTimeFrom": publish_from.isoformat(),
            "publishDateTimeTo": publish_to.isoformat(),
        }
        rows = await self._get("WINDFOR", params, refresh)
        result = []
        for row in rows:
            if not row.get("startTime") or not row.get("publishTime") or row.get("generation") is None:
                continue
            try:
                target, published = parse_dt(row["startTime"]), parse_dt(row["publishTime"])
            except ValueError:
                continue
            if target_start <= target < target_end and publish_from <= published <= publish_to:
                result.append(row)
        return result
