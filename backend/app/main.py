import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="Wind Forecast Intelligence API", version="1.0.0")
origins = [x.strip() for x in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"service": "wind-forecast-intelligence", "docs": "/docs"}
