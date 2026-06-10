"""
converter-service/main.py
FastAPI application that wraps 3D model conversion as an HTTP microservice.
Deployed independently to Railway — not imported by Next.js.

Authentication: every request to /convert must include:
  Authorization: Bearer <CONVERTER_SECRET>

Environment variables required:
  CONVERTER_SECRET  — shared secret for auth
  PORT              — set automatically by Railway

NEW DESIGN (v2):
  /convert now accepts the file as a multipart upload and returns the
  converted GLB as a binary response body.
  Next.js handles all Supabase uploads — the converter is a pure
  transformation service with zero Supabase dependency.
"""

import os
import asyncio
import tempfile
import logging
from datetime import datetime

# Load .env for local development — use __file__ so this works regardless of
# which directory the service is launched from (e.g. project root vs service dir)
from pathlib import Path
from dotenv import load_dotenv
_ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=False)

from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File, Form
from fastapi.responses import Response
import httpx

# Local converter logic
from converter import convert_file

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Craftit 3D Converter Service", version="2.0.0")

CONVERTER_SECRET = os.environ.get("CONVERTER_SECRET", "")


# ── Auth dependency ───────────────────────────────────────────────────────────
def verify_token(authorization: str = Header(...)):
    if not CONVERTER_SECRET:
        raise HTTPException(status_code=500, detail="Server misconfiguration: CONVERTER_SECRET not set")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[len("Bearer "):]
    if token != CONVERTER_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: invalid token")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat(), "version": "2.0.0"}


# ── Startup diagnostic ────────────────────────────────────────────────────────
@app.on_event("startup")
async def _startup_check():
    logger.info(f"[Converter] v2 started — pure transform service (no Supabase dependency)")
    logger.info(f"[Converter] .env path: {_ENV_FILE} (exists={_ENV_FILE.exists()})")
    logger.info(f"[Converter] CONVERTER_SECRET configured: {'yes' if CONVERTER_SECRET else 'NO - auth will fail!'}")


# ── Conversion endpoint ───────────────────────────────────────────────────────
# Accepts a file upload, converts it, and returns the GLB binary directly.
# Next.js is responsible for uploading the result to Supabase Storage.
@app.post("/convert")
async def convert(
    file: UploadFile = File(...),
    original_filename: str = Form(default="model"),
    _=Depends(verify_token),
):
    input_suffix = Path(original_filename).suffix.lower() or ".bin"
    tmp_input = tempfile.NamedTemporaryFile(suffix=input_suffix, delete=False)
    tmp_output = tempfile.NamedTemporaryFile(suffix=".glb", delete=False)
    tmp_input.close()
    tmp_output.close()

    try:
        # 1. Write the uploaded file to a temp path
        file_bytes = await file.read()
        logger.info(f"Received file: {original_filename} ({len(file_bytes)} bytes)")
        with open(tmp_input.name, "wb") as f:
            f.write(file_bytes)

        # 2. Run the conversion (120-second timeout)
        logger.info(f"Starting conversion: {tmp_input.name} -> {tmp_output.name}")
        try:
            await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, convert_file, tmp_input.name, tmp_output.name
                ),
                timeout=120,
            )
        except asyncio.TimeoutError:
            logger.error("Conversion timed out after 120s")
            raise HTTPException(status_code=422, detail="Conversion timed out after 120 seconds")
        except Exception as conv_err:
            logger.error(f"Conversion failed: {conv_err}")
            raise HTTPException(status_code=422, detail=f"Conversion failed: {str(conv_err)}")

        # 3. Read result and return as binary response
        with open(tmp_output.name, "rb") as f:
            glb_data = f.read()

        logger.info(f"Conversion complete. Output size: {len(glb_data)} bytes")
        return Response(
            content=glb_data,
            media_type="model/gltf-binary",
            headers={"X-Converted-Size": str(len(glb_data))},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during conversion")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 4. Clean up temp files
        for tmp in [tmp_input.name, tmp_output.name]:
            try:
                os.unlink(tmp)
            except OSError:
                pass
