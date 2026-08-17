@echo off
start "" ollama serve
timeout /t 2 >nul
set OLLAMA_TURBO_MODEL=qwen2.5-coder:7b
set OLLAMA_EXPERT_MODEL=gpt-oss:20b
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
