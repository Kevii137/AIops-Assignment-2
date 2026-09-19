import hashlib
import os

import joblib
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

MODEL_PATH = os.environ.get("MODEL_PATH", "/app/model.joblib")
APP_VERSION = os.environ.get("APP_VERSION", "v2")
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "60"))

app = FastAPI(title="Spam Detection API")
_pipeline = None
_redis = None


@app.on_event("startup")
def load_model():
    global _pipeline, _redis
    _pipeline = joblib.load(MODEL_PATH)
    if REDIS_HOST:
        import redis
        _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    print(f"Loaded model from {MODEL_PATH} (version={APP_VERSION}, cache={'on' if _redis else 'off'})")


class PredictRequest(BaseModel):
    text: str


def _cache_key(text: str) -> str:
    return "predict:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@app.get("/healthz")
def healthz():
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="model not loaded")
    return {"status": "ok", "version": APP_VERSION}


@app.post("/predict")
def predict(request: PredictRequest, response: Response):
    if _redis is not None:
        key = _cache_key(request.text)
        cached = _redis.get(key)
        if cached is not None:
            response.headers["X-Cache"] = "HIT"
            return {"label": cached}
        label = str(_pipeline.predict([request.text])[0])
        _redis.setex(key, CACHE_TTL_SECONDS, label)
        response.headers["X-Cache"] = "MISS"
        return {"label": label}

    label = str(_pipeline.predict([request.text])[0])
    return {"label": label}
