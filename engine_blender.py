# engine_blender.py — DISABLED (kept for future re-enabling)
#
# Blender requires a system Blender installation which is not available
# on Railway's Nixpacks build. Re-enable when a Blender-capable environment
# is available.
#
# To re-enable:
# 1. Uncomment the code below.
# 2. Add "blender" to the converter.py routing logic.
# 3. Ensure BLENDER_PATH env var points to the Blender executable.

# import subprocess
# import os
#
# def convert_blender(input_path, output_path):
#     script_dir = os.path.dirname(os.path.abspath(__file__))
#     export_script = os.path.join(script_dir, "blender_export.py")
#     blender_bin = os.environ.get("BLENDER_PATH", "blender")
#     command = [blender_bin, "--background", "--python", export_script, "--", input_path, output_path]
#     try:
#         result = subprocess.run(command, capture_output=True, text=True, check=True)
#         print(f"Blender conversion complete for {input_path}")
#         print(result.stdout)
#     except subprocess.CalledProcessError as e:
#         raise RuntimeError(f"Blender conversion failed:\n{e.stdout}\n{e.stderr}")
#     except FileNotFoundError:
#         raise FileNotFoundError("Blender executable not found. Set BLENDER_PATH env var.")
