from math import sqrt
from statistics import mean

def calculate_accuracy(rows: list[dict]) -> dict:
    matched = [r for r in rows if r.get("forecast_mw") is not None and r.get("actual_mw") is not None]
    errors = [float(r["forecast_mw"]) - float(r["actual_mw"]) for r in matched]
    abs_errors = [abs(e) for e in errors]
    nonzero = [(float(r["forecast_mw"]), float(r["actual_mw"])) for r in matched if float(r["actual_mw"]) != 0]
    return {
        "mae_mw": mean(abs_errors) if errors else None,
        "rmse_mw": sqrt(mean(e*e for e in errors)) if errors else None,
        "mbe_mw": mean(errors) if errors else None,
        "mape_pct": mean(abs(f-a)/abs(a) for f,a in nonzero)*100 if nonzero else None,
        "matched_intervals": len(matched),
        "missing_forecasts": sum(r.get("forecast_mw") is None for r in rows),
        "missing_actuals": sum(r.get("actual_mw") is None for r in rows),
        "mape_nonzero_actual_intervals": len(nonzero),
        "error_convention": "forecast_minus_actual",
    }
