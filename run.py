import sys
import subprocess
from pathlib import Path
import uvicorn

root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"
sys.path.insert(0, str(backend_dir))


def run_backend():
    print("[Backend] Starting FastAPI server on http://127.0.0.1:8000 ...")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        app_dir=str(backend_dir)
    )


def run_streamlit():
    print("[Frontend] Starting Streamlit dashboard on http://localhost:8501 ...")
    streamlit_path = root_dir / "streamlit_app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(streamlit_path), "--server.port", "8501"]
    subprocess.run(cmd)


def run_both():
    import threading
    import time
    print("[Meeting Intelligence] Launching both FastAPI backend and Streamlit...")
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    time.sleep(1.5)
    run_streamlit()


if __name__ == "__main__":
    if "--streamlit" in sys.argv:
        run_streamlit()
    elif "--all" in sys.argv:
        run_both()
    else:
        run_backend()
