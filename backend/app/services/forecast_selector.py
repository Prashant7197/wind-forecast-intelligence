from datetime import datetime, timezone

def normalize_datetime(value: str | datetime) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)

def select_forecasts(records: list[dict], cutoff: datetime, target_start: datetime, target_end: datetime) -> list[dict]:
    cutoff, target_start, target_end = normalize_datetime(cutoff), normalize_datetime(target_start), normalize_datetime(target_end)
    latest, latest_pub = {}, {}
    for row in records:
        if not row.get("startTime") or not row.get("publishTime") or row.get("generation") is None:
            continue
        try:
            target = normalize_datetime(row["startTime"])
            published = normalize_datetime(row["publishTime"])
            generation = float(row["generation"])
        except (ValueError, TypeError):
            continue
        if not target_start <= target < target_end or published > cutoff:
            continue
        key = target.isoformat()
        if key not in latest_pub or published > latest_pub[key]:
            latest_pub[key] = published
            latest[key] = {**row, "startTime": key, "publishTime": published.isoformat(), "generation": generation}
    return sorted(latest.values(), key=lambda row: row["startTime"])
