"""UniScholar Analytics entry point runner."""
import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    is_dev = os.environ.get("ENV", "development").lower() != "production"
    print(f"============================================================")
    print(f"  UniScholar Research Analytics Dashboard is starting...")
    print(f"  Binding: http://{host}:{port}")
    print(f"============================================================")
    uvicorn.run("server:app", host=host, port=port, reload=is_dev)
