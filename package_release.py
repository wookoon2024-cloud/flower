"""
Release Packaging Script for 마음지킴이 (AI Companion Plant)
Generates both:
1. 마음지킴이_실행파일_v{version}.zip (Portable EXE + config + docs)
2. 마음지킴이_소스_v{version}.zip (Complete source code package)
"""
import os
import zipfile
import hashlib
from ai_plant import __version__

VERSION = f"v{__version__}"

def create_release_packages():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_exe = os.path.join(base_dir, "dist", "마음지킴이.exe")
    
    if not os.path.exists(dist_exe):
        print(f"Error: {dist_exe} not found. Please run build_exe.py first.")
        return

    # 1. Standalone Executable ZIP
    exe_zip_name = f"마음지킴이_실행파일_{VERSION}.zip"
    exe_zip_path = os.path.join(base_dir, exe_zip_name)
    
    print(f"=== Creating Executable Release ZIP: {exe_zip_name} ===")
    with zipfile.ZipFile(exe_zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(dist_exe, "마음지킴이.exe")
        print(f"  + Added: 마음지킴이.exe ({os.path.getsize(dist_exe):,} bytes)")
        
        config_path = os.path.join(base_dir, "config.json")
        if os.path.exists(config_path):
            zipf.write(config_path, "config.json")
            print("  + Added: config.json")
            
        readme_path = os.path.join(base_dir, "README.md")
        if os.path.exists(readme_path):
            zipf.write(readme_path, "README.md")
            print("  + Added: README.md")

    # 2. Complete Clean Source Code ZIP
    src_zip_name = f"마음지킴이_소스_{VERSION}.zip"
    src_zip_path = os.path.join(base_dir, src_zip_name)
    
    print(f"\n=== Creating Source Code Release ZIP: {src_zip_name} ===")
    exclude_dirs = {".git", ".venv", "venv", "env", "build", "dist", "__pycache__", ".idea", ".vscode", "releases"}
    exclude_exts = {".pyc", ".pyd", ".pyo", ".zip", ".spec"}

    with zipfile.ZipFile(src_zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                if file.startswith("test_") and file.endswith((".db", ".json")):
                    continue
                abs_f = os.path.join(root, file)
                rel_f = os.path.relpath(abs_f, base_dir)
                zipf.write(abs_f, rel_f)
        print(f"  + Source code archive created with {len(zipf.namelist())} files.")

    print(f"\n[Packaging Completed]")
    print(f"1. {exe_zip_name} ({os.path.getsize(exe_zip_path):,} bytes)")
    print(f"2. {src_zip_name} ({os.path.getsize(src_zip_path):,} bytes)")

if __name__ == "__main__":
    create_release_packages()
