"""
converter-service/converter.py
Orchestrator — detects format and routes to the appropriate engine.
Adapted from python-converters/converter.py to be callable as a function (not subprocess).
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)


def detect_format(filename):
    """Map file extension to conversion engine name."""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {
        ".stl": "trimesh",
        ".obj": "trimesh",
        ".ply": "trimesh",
        ".glb": "trimesh",
        ".gltf": "trimesh",
        # Blender and CAD engines are kept but disabled pending deployment dependencies
        ".fbx": "blender",
        ".blend": "blender",
        ".step": "cad",
        ".stp": "cad",
        ".iges": "cad",
        ".igs": "cad",
        ".x_t": "cad",
        ".x_b": "cad",
    }
    if ext in mapping:
        return mapping[ext]
    raise ValueError(
        f"Unsupported file format: {ext}. "
        "Supported: STL, OBJ, PLY, GLB, GLTF (FBX, BLEND, STEP, IGES disabled)."
    )


def convert_file(input_path, output_path):
    """
    Route-and-run conversion. Raises on failure.
    Currently only trimesh engine is active; blender/cad remain disabled.
    """
    engine_type = detect_format(input_path)
    print(f"[Converter] Detected engine: {engine_type.upper()}")

    if engine_type == "trimesh":
        from engine_trimesh import convert_trimesh
        convert_trimesh(input_path, output_path)
    elif engine_type in ("blender", "cad"):
        raise ValueError(
            f"Engine '{engine_type}' is currently disabled. "
            "Only trimesh-compatible formats (STL, OBJ, PLY, GLB, GLTF) are supported."
        )
    else:
        raise ValueError(f"Unrecognized engine type: {engine_type}")
