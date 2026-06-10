# engine_cad.py — DISABLED (kept for future re-enabling)
#
# CAD engine requires pythonocc-core which has complex system-level dependencies
# (OpenCASCADE) that are difficult to install on Railway's Nixpacks.
# Re-enable when a suitable environment (e.g., conda-based Docker) is available.
#
# Supported formats when enabled: .step, .stp, .iges, .igs
# Parasolid (.x_t, .x_b) support is NOT implemented.
#
# To re-enable:
# 1. Uncomment the code below.
# 2. Add pythonocc-core to requirements.txt (conda preferred).
# 3. Update converter.py to route "cad" engine to convert_cad().

# import os
# import numpy as np
# import trimesh
# from OCC.Core.STEPControl import STEPControl_Reader
# from OCC.Core.IGESControl import IGESControl_Reader
# from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
# from OCC.Core.TopExp import TopExp_Explorer
# from OCC.Core.TopAbs import TopAbs_FACE
# from OCC.Core.BRep import BRep_Tool
# from OCC.Core.TopLoc import TopLoc_Location
# from OCC.Core.IFSelect import IFSelect_RetDone
#
# def convert_cad(input_path, output_path):
#     ...  # See python-converters/engine_cad.py for full implementation
