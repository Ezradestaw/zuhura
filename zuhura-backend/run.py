import os
import sys
import traceback

print(">>> Starting Zuhura Backend run.py...", flush=True)
print(f">>> Python: {sys.version}", flush=True)
print(f">>> CWD: {os.getcwd()}", flush=True)
print(f">>> PORT: {os.environ.get('PORT')}", flush=True)

try:
    print(">>> Importing zuhura.api.main...", flush=True)
    from zuhura.api.main import app
    print(">>> Successfully loaded FastAPI application!", flush=True)
except Exception as e:
    print(f">>> FATAL ERROR IMPORTING MAIN: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    print(f">>> Starting uvicorn on 0.0.0.0:{port}...", flush=True)
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", access_log=True)
    except Exception as e:
        print(f">>> FATAL ERROR RUNNING UVICORN: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
