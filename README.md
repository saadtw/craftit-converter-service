# Craftit 3D Converter Service

A standalone FastAPI microservice that converts 3D model files (STL, OBJ, PLY) to GLB format using Trimesh. Deployed independently to Railway — not part of the Next.js build.

## How it works

1. The Next.js app uploads a raw 3D file to Supabase Storage.
2. It calls `POST /convert` on this service with the file's public URL.
3. This service downloads the file, converts it to GLB, re-uploads to Supabase Storage, and returns the final public URL.
4. The Next.js app deletes the original raw file.

## Running locally

```bash
cd converter-service
pip install -r requirements.txt
cp .env.example .env
# Fill in your values in .env
uvicorn main:app --reload --port 8000
```

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Test conversion:
```bash
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-here" \
  -d '{
    "input_url": "https://your-project.supabase.co/storage/v1/object/public/craftit-uploads/3d-models/raw/test.stl",
    "output_path": "3d-models/converted/test.glb",
    "supabase_url": "https://your-project.supabase.co",
    "supabase_service_key": "your-service-role-key"
  }'
```

## Required environment variables

| Variable | Description |
|---|---|
| `CONVERTER_SECRET` | Shared secret to authenticate incoming requests |
| `SUPABASE_SECRET_KEY` | Supabase secret key (has storage write access) |
| `PORT` | API port (Railway sets this automatically) |

## Deploying to Railway

1. Push the entire `craftit/` monorepo to GitHub.
2. Create a **new Railway project** → Deploy from GitHub repo.
3. In Railway project settings → **Root Directory** → set to `converter-service`.
4. Railway will auto-detect Python via Nixpacks and install `requirements.txt`.
5. Set environment variables in the Railway dashboard:
   - `CONVERTER_SECRET` (generate a random string)
   - `NIXPACKS_PYTHON_VERSION=3.11` (recommended)
6. After deployment, copy the Railway URL (e.g. `https://craftit-converter.railway.app`) and set it as `CONVERTER_SERVICE_URL` in your main Next.js Vercel project.

> **Note:** This service runs in the same GitHub repository as the Next.js app but is deployed as a completely separate Railway service. It communicates with the Next.js app only via HTTP — there are no shared imports.

## Supported formats

| Format | Engine | Status |
|---|---|---|
| `.stl`, `.obj`, `.ply`, `.glb`, `.gltf` | Trimesh | ✅ Active |
| `.fbx`, `.blend` | Blender | ⛔ Disabled (no Blender on Railway) |
| `.step`, `.iges`, `.stp`, `.igs` | CAD (pythonocc) | ⛔ Disabled (complex deps) |
