from datetime import date, datetime, time, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from app.services.elexon_client import ElexonClient, ElexonDataError
from app.services.forecast_selector import select_forecasts
from app.services.accuracy import calculate_accuracy

router = APIRouter()
client = ElexonClient()

def ensure_january(value: date):
    if value.year != 2026 or value.month != 1:
        raise HTTPException(status_code=422, detail="Only January 2026 delivery dates are in scope.")

def as_utc(value: datetime):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

@router.get("/health")
def health():
    return {"status": "ok", "service": "wind-forecast-intelligence-api"}

@router.get("/delivery-days")
def delivery_days():
    return {"dates": [(date(2026, 1, 1) + timedelta(days=i)).isoformat() for i in range(31)], "timezone": "UTC"}

@router.get("/series")
async def series(delivery_date: date = Query(...), cutoff: datetime | None = Query(None), refresh: bool = Query(False)):
    ensure_january(delivery_date)
    start = datetime.combine(delivery_date, time.min, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    decision_cutoff = as_utc(cutoff) if cutoff else start - timedelta(hours=12)
    publish_from = start - timedelta(days=1)
    try:
        actuals = await client.fetch_actuals(start, end, refresh)
        forecasts = await client.fetch_forecasts(start, end, publish_from, decision_cutoff, refresh)
    except ElexonDataError as exc:
        raise HTTPException(status_code=502, detail=f"Elexon request failed: {exc}") from exc

    selected = select_forecasts(forecasts, decision_cutoff, start, end)
    actual_map = {}
    for row in actuals:
        if row.get("startTime") and row.get("generation") is not None:
            actual_map[_iso(row["startTime"])] = float(row["generation"])
    forecast_map = {row["startTime"]: row for row in selected}
    keys = sorted(set(actual_map) | set(forecast_map))
    points = []
    for key in keys:
        f = forecast_map.get(key)
        fv = float(f["generation"]) if f and f.get("generation") is not None else None
        av = actual_map.get(key)
        err = fv - av if fv is not None and av is not None else None
        points.append({"startTime": key, "forecast_mw": fv, "actual_mw": av, "error_mw": err,
                       "absolute_error_mw": abs(err) if err is not None else None,
                       "publishTime": f.get("publishTime") if f else None})
    return {
        "delivery_date": delivery_date.isoformat(), "decision_cutoff": decision_cutoff.isoformat(),
        "cutoff_assumption": "Default is 12:00 UTC on the preceding day; this is illustrative, not a confirmed market deadline.",
        "source": "Elexon FUELHH (WIND) + WINDFOR", "unit": "MW", "expected_intervals": 48,
        "returned_intervals": len(points), "selected_forecast_records": len(selected),
        "actual_records": len(actual_map), "metrics": calculate_accuracy(points), "series": points,
        "data_note": "Metrics use matched intervals only. Missing values are not treated as zero. Verify live endpoint schema and historical coverage."
    }

@router.get("/accuracy")
async def accuracy(delivery_date: date = Query(...), cutoff: datetime | None = Query(None), refresh: bool = Query(False)):
    result = await series(delivery_date, cutoff, refresh)
    return {k: result[k] for k in ("delivery_date", "decision_cutoff", "metrics", "expected_intervals", "returned_intervals", "selected_forecast_records", "actual_records")}

@router.get("/forecast")
async def forecast(delivery_date: date = Query(...), cutoff: datetime | None = Query(None), refresh: bool = Query(False)):
    result = await series(delivery_date, cutoff, refresh)
    return {"delivery_date": result["delivery_date"], "decision_cutoff": result["decision_cutoff"],
            "series": [{"startTime": r["startTime"], "generation": r["forecast_mw"], "publishTime": r["publishTime"]} for r in result["series"] if r["forecast_mw"] is not None]}

@router.get("/actuals")
async def actuals(delivery_date: date = Query(...), refresh: bool = Query(False)):
    result = await series(delivery_date, refresh=refresh)
    return {"delivery_date": result["delivery_date"], "series": [{"startTime": r["startTime"], "generation": r["actual_mw"]} for r in result["series"] if r["actual_mw"] is not None]}

def _iso(value: str):
    from app.services.forecast_selector import normalize_datetime
    return normalize_datetime(value).isoformat()
