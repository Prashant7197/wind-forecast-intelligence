from datetime import datetime
from app.services.forecast_selector import select_forecasts

def dt(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))

def test_latest_eligible_forecast_only():
    rows = [
        {"startTime":"2026-01-15T00:00:00Z","publishTime":"2026-01-14T08:00:00Z","generation":80},
        {"startTime":"2026-01-15T00:00:00Z","publishTime":"2026-01-14T11:00:00Z","generation":90},
        {"startTime":"2026-01-15T00:00:00Z","publishTime":"2026-01-14T13:00:00Z","generation":999},
    ]
    selected = select_forecasts(rows, dt("2026-01-14T12:00:00Z"), dt("2026-01-15T00:00:00Z"), dt("2026-01-16T00:00:00Z"))
    assert len(selected) == 1 and selected[0]["generation"] == 90

def test_outside_target_and_missing_values_ignored():
    rows = [
        {"startTime":"2026-01-16T00:00:00Z","publishTime":"2026-01-14T11:00:00Z","generation":90},
        {"startTime":"2026-01-15T00:00:00Z","publishTime":"2026-01-14T11:00:00Z","generation":None},
    ]
    assert select_forecasts(rows, dt("2026-01-14T12:00:00Z"), dt("2026-01-15T00:00:00Z"), dt("2026-01-16T00:00:00Z")) == []
