"""UniScholar Analytics entry point runner."""
import os
from pathlib import Path
import sys
import uvicorn

if __name__ == "__main__":
    app_dir = Path(__file__).resolve().parent
    os.chdir(app_dir)
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    use_reload = os.environ.get("RELOAD", "false").lower() == "true"
    print(f"============================================================")
    print(f"  UniScholar Research Analytics Dashboard is starting...")
    print(f"  Local URL: http://127.0.0.1:{port}")
    print(f"  Binding:   http://{host}:{port}")
    print(f"============================================================")
    uvicorn.run("server:app", host=host, port=port, reload=use_reload, app_dir=str(app_dir))
