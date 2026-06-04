import os
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup checks
    model_name = os.getenv("MODEL_NAME", "llama3.1:8b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            if model_name not in models and f"{model_name}:latest" not in models and not any(m.startswith(model_name) for m in models):
                print(f"WARNING: Model '{model_name}' not found in Ollama. Please run 'ollama run {model_name}' to pull it.")
            else:
                print(f"SUCCESS: Connected to Ollama and found '{model_name}'.")
    except httpx.RequestError as e:
        print(f"CRITICAL ERROR: Could not connect to Ollama at {base_url}. Please ensure Ollama is running. Error: {e}")
    except Exception as e:
        print(f"WARNING: Failed to verify Ollama status: {e}")
        
    yield
    # Shutdown

app = FastAPI(
    title="LEXA API",
    description="Multi-agent legal reasoning system API",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.analyze import router as analyze_router
from api.test_model import router as test_model_router
app.include_router(analyze_router, prefix="/api/v1")
app.include_router(test_model_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "LEXA API is running"}
