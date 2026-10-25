from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ai_controller import process_command

app = FastAPI(title="SAP AI Chat POC")
ROOT = Path(__file__).resolve().parent
sap_lock = Lock()  # Egy SAP sessiont ne vezéreljen egyszerre két kérés.


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")


@app.post("/api/chat")
def chat(request: ChatRequest):
    command = request.message.strip()
    if not command:
        raise HTTPException(status_code=400, detail="Üres üzenet")

    # A FastAPI sync végpontját worker thread szolgálja ki.
    # A SAP GUI Scripting COM interfészét ebben a szálban inicializáljuk.
    try:
        import pythoncom
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="Hiányzik a pywin32 csomag.") from exc

    pythoncom.CoInitialize()
    try:
        with sap_lock:
            reply = process_command(command)
        return {"reply": str(reply)}
    except Exception as exc:
        # POC: hibaüzenet megjelenítése a felületen, szerverlogban is.
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"SAP feldolgozási hiba: {exc}") from exc
    finally:
        pythoncom.CoUninitialize()
