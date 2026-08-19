"""
Release Packaging Script
Compresses standalone executable, config, assets, and documentation into a versioned portable zip package.
"""
import os
import zipfile
import hashlib

VERSION = "v1.0.0"
RELEASE_DIR = "releases"
ZIP_NAME = f"AI_Companion_Plant_{VERSION}_Portable.zip"

def create_release_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_exe = os.path.join(base_dir, "dist", "AICompanionPlant.exe")
    
    if not os.path.exists(dist_exe):
        print(f"Error: {dist_exe} not found. Please run build_exe.py first.")
        return

    os.makedirs(os.path.join(base_dir, RELEASE_DIR), exist_ok=True)
    zip_path = os.path.join(base_dir, RELEASE_DIR, ZIP_NAME)

    files_to_pack = [
        ("dist/AICompanionPlant.exe", "AICompanionPlant.exe"),
        ("config.json", "config.json"),
        ("README.md", "README.md"),
        ("INSTALL_GUIDE.md", "INSTALL_GUIDE.md")
    ]

    print(f"Creating release archive: {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for rel_src, arcname in files_to_pack:
            abs_src = os.path.join(base_dir, rel_src)
            if os.path.exists(abs_src):
                zipf.write(abs_src, arcname)
                print(f"  + Added: {arcname} ({os.path.getsize(abs_src):,} bytes)")

    # Calculate SHA256
    sha256 = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    print(f"\n[Release Packaged Successfully]")
    print(f"File: {zip_path}")
    print(f"Size: {os.path.getsize(zip_path):,} bytes")
    print(f"SHA-256: {checksum}")

    # Write checksum file
    with open(os.path.join(base_dir, RELEASE_DIR, f"{ZIP_NAME}.sha256"), "w", encoding="utf-8") as f:
        f.write(f"{checksum} *{ZIP_NAME}\n")

if __name__ == "__main__":
    create_release_zip()
