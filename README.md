# Wind Forecast Intelligence

React + TypeScript + Vite frontend and Python/FastAPI backend for the UK national wind forecast assessment.

## Features
- January 2026 delivery-date and decision-cutoff selection.
- Elexon FUELHH wind actuals and WINDFOR forecasts.
- Latest eligible forecast per delivery interval, constrained by `publishTime <= cutoff`.
- Forecast/actual chart, interval table, CSV export, MAE, RMSE, bias and MAPE.
- Missing data is not replaced with zero; synthetic records are used only in unit tests.
- Docker Compose, tests, deployment notes, and API health endpoint.

## Important methodology
The assignment does not specify the exact decision cutoff. The default is noon UTC on the preceding day as an explicit illustrative assumption, and the UI allows a cutoff to be selected. Confirm the client's actual trading cutoff before interpreting results. Forecasts are selected independently for each target interval to avoid look-ahead bias. Error is defined as `forecast - actual`; positive bias means over-forecasting.

The API client targets `https://data.elexon.co.uk/bmrs/api/v1/datasets/{FUELHH|WINDFOR}/stream`. Elexon API query parameters and response shape can change; verify the current live API documentation and run the app's data smoke test before relying on results. The client code isolates these parameters in `backend/app/services/elexon_client.py`. No fake observations are displayed when source retrieval fails.

## Architecture
```text
React/Vite/Recharts -> FastAPI -> Elexon client -> FUELHH/WINDFOR
                                      |
                         forecast selector + accuracy metrics
                                      |
                               JSON file cache
```

## Layout
- `frontend/src/`: React dashboard, chart, filters, CSV export and styling
- `backend/app/api/routes.py`: REST API
- `backend/app/services/elexon_client.py`: Elexon HTTP client and cache
- `backend/app/services/forecast_selector.py`: cutoff-aware forecast selection
- `backend/app/services/accuracy.py`: error metrics
- `backend/tests/`: unit tests
- `docker-compose.yml`: local container setup
- `DEPLOYMENT.md`: Vercel + Python API hosting checklist

## Run with Docker
Prerequisite: Docker Desktop / Docker Engine with Compose.
```bash
docker compose up --build
```
- UI: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Run locally without Docker
Backend:
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Frontend in another terminal:
```bash
cd frontend
npm install
npm run dev
```

## Tests
```bash
cd backend
pip install -r requirements.txt
pytest -q
```
Synthetic fixtures in tests verify algorithms only; they are not represented as Elexon data.

## Deployment
See `DEPLOYMENT.md`. This ZIP does not itself publish the GitHub repository, deploy services, or upload a YouTube video. After deploying, replace placeholder URLs with actual public links and test them in an incognito window.

## AI assistance disclosure
OpenAI ChatGPT was used to assist with requirements analysis, architecture, implementation scaffolding, test design, and documentation. Verify live Elexon API behavior and all deployed outputs before submission.

## Limitations
Only national wind actuals and forecasts are included. Demand, other generation, prices, imbalance costs, and plant constraints are excluded, so this tool does not calculate the complete procurement position. This is an assessment pilot, not a production trading system.
