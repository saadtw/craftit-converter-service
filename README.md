# Craftit 3D Converter Service

A standalone FastAPI microservice that converts 3D model files to **GLB format** using Trimesh. Deployed independently to Railway — completely separate from the Next.js frontend.

## Architecture

This is a **pure transformation service**. It accepts a raw 3D file as a multipart upload and returns the converted GLB as a binary response body. It has **no storage dependency** — all storage operations are handled by the caller (Next.js app).

```
Next.js App
  │
  ├─ Uploads raw file to Supabase Storage
  ├─ POST /convert  →  Converter Service (Railway)
  │     Receives: multipart file upload
  │     Returns:  GLB binary (model/gltf-binary)
  └─ Uploads GLB to Supabase Storage → deletes original
```

## API Reference

### `GET /health`

Returns service status and version. No authentication required.

```json
{ "status": "ok", "time": "2024-01-01T00:00:00", "version": "2.0.0" }
```

### `POST /convert`

Converts a 3D model file to GLB. Requires Bearer token authentication.

**Request:** `multipart/form-data`

| Field               | Type   | Description                                             |
| ------------------- | ------ | ------------------------------------------------------- |
| `file`              | File   | The 3D model file to convert                            |
| `original_filename` | string | Original filename (used for format/extension detection) |

**Headers:**

| Header          | Value                       |
| --------------- | --------------------------- |
| `Authorization` | `Bearer <CONVERTER_SECRET>` |

**Response:** Raw GLB binary (`model/gltf-binary`) with `X-Converted-Size` header indicating output size in bytes.

**Example:**

```bash
curl -X POST http://localhost:8000/convert \
  -H "Authorization: Bearer your-secret-here" \
  -F "file=@model.stl" \
  -F "original_filename=model.stl" \
  --output model.glb
```

**Error codes:**

| Code | Meaning                                      |
| ---- | -------------------------------------------- |
| 401  | Missing or malformed `Authorization` header  |
| 403  | Invalid token                                |
| 422  | Conversion failed or timed out (120 s limit) |
| 500  | Server error or `CONVERTER_SECRET` not set   |

## Supported Formats

| Format                                  | Engine  | Status      |
| --------------------------------------- | ------- | ----------- |
| `.stl`, `.obj`, `.ply`, `.glb`, `.gltf` | Trimesh | ✅ Active   |
| `.fbx`, `.blend`                        | Blender | ⛔ Disabled |
| `.step`, `.stp`, `.iges`, `.igs`        | CAD     | ⛔ Disabled |

### Trimesh engine features

- **Axis correction:** STL/PLY files (Z-up) are rotated to Y-up for correct GLB display.
- **Texture downscaling:** Oversized textures are downscaled to 1024×1024 (LANCZOS).
- **Mesh decimation:** Meshes exceeding 300,000 faces are simplified via a 3-tier fallback:
  1. Quadratic decimation (Trimesh built-in)
  2. Module-level API (alternate signature)
  3. Vertex clustering (always works, no extra deps)

## Running Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in CONVERTER_SECRET in .env
uvicorn main:app --reload --port 8000
```

Test the health endpoint:

```bash
curl http://localhost:8000/health
```

Test conversion:

```bash
curl -X POST http://localhost:8000/convert \
  -H "Authorization: Bearer your-secret-here" \
  -F "file=@model.stl" \
  -F "original_filename=model.stl" \
  --output model.glb
```

## Environment Variables

| Variable           | Description                                                         |
| ------------------ | ------------------------------------------------------------------- |
| `CONVERTER_SECRET` | Shared secret — must match `CONVERTER_SECRET` in the Next.js app    |
| `PORT`             | API port (set automatically by Railway; defaults to `8000` locally) |

> **Optional:** Set `NIXPACKS_PYTHON_VERSION=3.11` in the Railway dashboard to pin the Python version.

## Deploying to Railway

1. Push this repository to GitHub.
2. Create a **new Railway project** → **Deploy from GitHub repo**.
3. Railway auto-detects Python via Nixpacks and installs `requirements.txt`.
4. The start command is defined in `railway.toml`:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Set environment variables in the Railway dashboard:
   - `CONVERTER_SECRET` — generate a random secret string
   - `NIXPACKS_PYTHON_VERSION=3.11` (recommended)
6. Copy the Railway deployment URL and set it as `CONVERTER_SERVICE_URL` in your Next.js Vercel project.

## Tech Stack

| Layer          | Technology                       |
| -------------- | -------------------------------- |
| Framework      | FastAPI 0.109+                   |
| Server         | Uvicorn 0.27+                    |
| Conversion     | Trimesh 4.0+, NumPy 1.26+, SciPy |
| Simplification | fast-simplification              |
| Textures       | Pillow 10+                       |
| HTTP Client    | HTTPX                            |
| Deployment     | Railway (Nixpacks / Python)      |

## Related Repositories

- **Main App (Next.js):** [saadtw/craftit](https://github.com/saadtw/craftit)
