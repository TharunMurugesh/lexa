from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="LEXA API",
    description="Autonomous multi-agent courtroom intelligence API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import router

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "LEXA API is running", "mode": "mock-ready"}
