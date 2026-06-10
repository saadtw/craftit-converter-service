"""
converter-service/engine_trimesh.py
Trimesh-based conversion engine — copied and adapted from python-converters/engine_trimesh.py.
Handles: .stl, .obj, .ply, .glb, .gltf
"""

import os
import gc

import numpy as np
import trimesh
from PIL import Image


def process_material(mat):
    """Downscale oversized textures within a material to 1024×1024."""
    attrs = [
        "image",
        "baseColorTexture",
        "metallicRoughnessTexture",
        "normalTexture",
        "emissiveTexture",
        "occlusionTexture",
    ]
    for attr in attrs:
        if hasattr(mat, attr):
            img = getattr(mat, attr)
            if isinstance(img, Image.Image):
                if img.width > 1024 or img.height > 1024:
                    print(
                        f"[Trimesh] Downscaling texture "
                        f"{img.width}x{img.height} -> 1024x1024 (LANCZOS)"
                    )
                    img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)


# Rotation matrix: Z-up (STL/OBJ default) → Y-up (GLB/GLTF requirement)
# Rotates -90° around the X axis so Z becomes Y.
_Z_UP_TO_Y_UP = trimesh.transformations.rotation_matrix(
    angle=-np.pi / 2,
    direction=[1, 0, 0],
    point=[0, 0, 0],
)

# Formats that use Z-up convention and need the rotation applied
_Z_UP_FORMATS = {".stl", ".ply"}


def convert_trimesh(input_path, output_path):
    """
    Load input model with trimesh and export as GLB.
    Applies texture downscaling and mesh decimation for large meshes.
    Corrects axis orientation for Z-up formats (STL, PLY) to Y-up (GLB).
    """
    loaded = None
    scene = None
    try:
        ext = os.path.splitext(input_path)[1].lower()
        print(f"[Trimesh] Loading {ext} file: {input_path}")
        loaded = trimesh.load(input_path, force="scene")  # always load as Scene

        # loaded is now always a Scene
        if not isinstance(loaded, trimesh.Scene):
            # Wrap a bare Trimesh in a scene
            scene = trimesh.Scene()
            scene.add_geometry(loaded)
        else:
            scene = loaded

        if len(scene.geometry) == 0:
            raise ValueError("Loaded scene is empty — no geometry found.")

        # ── Axis correction for Z-up formats ─────────────────────────────────
        # STL/PLY files have no embedded coordinate system info.
        # Trimesh loads them in their native Z-up space; GLB requires Y-up.
        if ext in _Z_UP_FORMATS:
            print(f"[Trimesh] Applying Z-up -> Y-up axis correction for {ext}")
            scene.apply_transform(_Z_UP_TO_Y_UP)

        # ── Texture downscaling ───────────────────────────────────────────────
        for mesh in scene.geometry.values():
            if hasattr(mesh, "visual"):
                vis = mesh.visual
                if hasattr(vis, "material"):
                    process_material(vis.material)
                elif hasattr(vis, "materials"):
                    for mat in vis.materials:
                        process_material(mat)

        # ── Mesh decimation for very high-poly models ─────────────────────────
        for name, mesh in list(scene.geometry.items()):
            if not isinstance(mesh, trimesh.Trimesh):
                continue
            original_faces = len(mesh.faces)
            if original_faces > 300_000:
                print(f"[Trimesh] Decimating '{name}': {original_faces} -> 300000 faces")
                simplified = None
                # Tier 1: quadratic decimation (needs scipy)
                try:
                    simplified = mesh.simplify_quadric_decimation(face_count=300_000)
                    print(f"[Trimesh] Quadratic decimation OK: {len(simplified.faces)} faces")
                except Exception as e1:
                    print(f"[Trimesh] Quadratic decimation failed ({e1}), trying module-level call")
                    # Tier 2: trimesh module-level API (alternate signature)
                    try:
                        simplified = trimesh.simplify_quadric_decimation(mesh, face_count=300_000)
                        print(f"[Trimesh] Module-level decimation OK: {len(simplified.faces)} faces")
                    except Exception as e2:
                        print(f"[Trimesh] Module-level decimation failed ({e2}), using vertex clustering")
                        # Tier 3: vertex clustering — always works, no extra deps
                        # cell_size is roughly mesh_extent / desired_voxel_count
                        try:
                            extent = mesh.bounding_box.extents
                            cell_size = float(max(extent)) / 150.0  # ~150 divisions per axis
                            simplified = mesh.simplify_vertex_clustering(cell_size)
                            print(f"[Trimesh] Vertex clustering OK: {len(simplified.faces)} faces")
                        except Exception as e3:
                            print(f"[Trimesh] All decimation methods failed ({e3}) — skipping")
                if simplified is not None:
                    scene.geometry[name] = simplified

        # ── Export as GLB ─────────────────────────────────────────────────────
        scene.export(output_path, file_type="glb")
        print(f"[Trimesh] Success: exported to {output_path}")

    except Exception as e:
        print(f"[Trimesh] Error converting {input_path}: {e}")
        raise
    finally:
        if loaded is not None:
            del loaded
        if scene is not None:
            del scene
        gc.collect()
