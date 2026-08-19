"""
PyInstaller Build Automation Script for AI Companion Plant Widget
Produces a standalone single executable in dist/AICompanionPlant.exe
"""
import os
import sys
import subprocess
import shutil

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=== [1/3] Generating PNG and ICO assets ===")
    import generate_assets
    generate_assets.create_assets(os.path.join(base_dir, "assets"))

    print("=== [2/3] Running PyInstaller build ===")
    icon_path = os.path.join(base_dir, "assets", "app_icon.ico")
    assets_src = os.path.join(base_dir, "assets")

    # PyInstaller arguments
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir", # We will build onedir and/or onefile; onedir starts faster, onefile is convenient. Let's do onefile as requested
        "--onefile",
        "--windowed",
        f"--name=AICompanionPlant",
        f"--icon={icon_path}",
        f"--add-data={assets_src};assets",
        f"--hidden-import=PySide6",
        f"--hidden-import=requests",
        f"--hidden-import=sqlite3",
        "main.py"
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n=== [3/3] Build SUCCESS! ===")
        exe_path = os.path.join(base_dir, "dist", "AICompanionPlant.exe")
        print(f"Standalone Executable created at: {exe_path}")
        
        # Copy config.json to dist directory for user convenience
        config_src = os.path.join(base_dir, "config.json")
        config_dst = os.path.join(base_dir, "dist", "config.json")
        if os.path.exists(config_src):
            shutil.copy2(config_src, config_dst)
            print(f"Copied config.json to: {config_dst}")
    else:
        print(f"\nBuild FAILED with return code {result.returncode}")

if __name__ == "__main__":
    build()
