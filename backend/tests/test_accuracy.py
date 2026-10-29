import pytest
from app.services.accuracy import calculate_accuracy

def test_metrics_and_bias_sign():
    m = calculate_accuracy([{"forecast_mw":120,"actual_mw":100},{"forecast_mw":80,"actual_mw":100}])
    assert m["mae_mw"] == pytest.approx(20)
    assert m["rmse_mw"] == pytest.approx(20)
    assert m["mbe_mw"] == pytest.approx(0)

def test_missing_and_zero_actual_handling():
    m = calculate_accuracy([{"forecast_mw":100,"actual_mw":0},{"forecast_mw":None,"actual_mw":5},{"forecast_mw":8,"actual_mw":10}])
    assert m["matched_intervals"] == 2
    assert m["missing_forecasts"] == 1
    assert m["mape_nonzero_actual_intervals"] == 1
    assert m["mape_pct"] == pytest.approx(20)
