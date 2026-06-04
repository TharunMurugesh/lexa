# LEXA (Legal Explainable AI)

Multi-agent legal reasoning framework for evidence analysis, adjudication, contradiction detection, and explainable AI.

## Project Structure
- `backend/`: FastAPI server with LangGraph/LangChain agents.
- `frontend/`: React + Vite + TailwindCSS application.
- `data/`: Local storage for cases, laws, and uploads.
- `docs/`: Project documentation.

## Ollama Setup (Local LLM)
This project uses **Ollama** and the `llama3.1:8b` model entirely locally. No OpenAI APIs are used.

1. **Install Ollama**: Follow the instructions at [ollama.com](https://ollama.com/download) for your OS.
2. **Pull the Model**: Open your terminal and run:
   ```bash
   ollama run llama3.1:8b
   ```
   *This will download the model. You can exit the Ollama prompt once it finishes.*

## Startup Instructions

### Backend (FastAPI)
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The API will be available at http://localhost:8000. It will automatically check for Ollama on startup.

### Frontend (React/Vite)
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Load NVM and use Node 26 (if using NVM):
   ```bash
   export NVM_DIR="$HOME/.nvm"
   [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
   nvm use default
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
   The app will be available at http://localhost:5173.

## Testing the Model
You can independently verify that Ollama is connected by using the test endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/test-model \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is negligence?"}'
```
