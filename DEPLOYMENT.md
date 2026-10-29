# Deployment checklist

## GitHub
Create a public repository with a random/non-identifying name, then:
```bash
git init
git add .
git commit -m "Build wind forecast intelligence dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-RANDOM-REPO.git
git push -u origin main
```

## Backend (Render or another Python-capable host)
- Root directory: `backend`
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set `FRONTEND_ORIGIN=https://YOUR-APP.vercel.app`
- Set `ELEXON_API_BASE=https://data.elexon.co.uk/bmrs/api/v1`
- Set `CACHE_DIR=/tmp/wind-forecast-cache` or a persistent disk path.
- Verify `/api/health` and `/docs`.

## Frontend (Vercel)
- Root directory: `frontend`
- Framework: Vite
- Build: `npm run build`
- Output: `dist`
- Environment: `VITE_API_BASE_URL=https://YOUR-BACKEND-HOST`
- Redeploy after setting variables.

## Final checks
Open every public URL in incognito mode. Test a January 2026 delivery date, refresh data, inspect logs, verify CORS and ensure no placeholder URLs remain. Free hosts may sleep or have ephemeral filesystems.
