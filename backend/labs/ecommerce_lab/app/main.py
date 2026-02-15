"""
E-Commerce Lab: Unified T1+T2+T3 for qa-lab-ecommerce.fly.dev
Mounted at /t1, /t2, /t3
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def _get_t1_app():
    from app.t1.main import app
    return app
def _get_t2_app():
    from app.t2.main import app
    return app
def _get_t3_app():
    from app.t3.main import app
    return app

app = FastAPI(title="E-Commerce Lab", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health():
    return {"status": "healthy", "tiers": ["t1", "t2", "t3"], "base_urls": {"t1": "/t1", "t2": "/t2", "t3": "/t3"}}

app.mount("/t1", _get_t1_app())
app.mount("/t2", _get_t2_app())
app.mount("/t3", _get_t3_app())
