"""
Release Packaging Script for 마음지킴이 (AI Companion Plant)
Generates both:
1. 마음지킴이_실행파일_v{version}.zip (Portable EXE + 기본 config.json + README)
2. 마음지킴이_소스_v{version}.zip (git 에 등록된 소스만 – 개인 DB·로그·설정·제출자료 제외)

개인 데이터 보호: 실행 폴더의 plant_data.db / mind_keeper.db / mindkeeper_debug.log / 사용자 config.json 은
절대 배포 파일에 넣지 않는다. 실행파일 zip 의 config.json 은 기본값(DEFAULT_CONFIG)으로 새로 만든다.
"""
import os
import json
import zipfile
import subprocess
from ai_plant import __version__
from ai_plant.config import DEFAULT_CONFIG, SENSITIVE_KEYS

VERSION = f"v{__version__}"
PERSONAL_FILES = {"plant_data.db", "mind_keeper.db", "mindkeeper_debug.log"}


def clean_default_config() -> str:
    cfg = {k: v for k, v in DEFAULT_CONFIG.items() if k not in SENSITIVE_KEYS}
    return json.dumps(cfg, ensure_ascii=False, indent=4)


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
        zipf.writestr("config.json", clean_default_config())
        readme_path = os.path.join(base_dir, "README.md")
        if os.path.exists(readme_path):
            zipf.write(readme_path, "README.md")
        print("  + 마음지킴이.exe, config.json(기본값), README.md")

    # 2. Source ZIP – git 에 커밋된 파일만 (배포 zip·releases 제외)
    src_zip_name = f"마음지킴이_소스_{VERSION}.zip"
    src_zip_path = os.path.join(base_dir, src_zip_name)
    print(f"\n=== Creating Source Code Release ZIP: {src_zip_name} ===")
    subprocess.run(["git", "archive", "--format=zip", "-o", src_zip_path, "HEAD", "--", ".",
                    ":(exclude)*.zip", ":(exclude)releases"], cwd=base_dir, check=True)
    with zipfile.ZipFile(src_zip_path) as z:
        names = z.namelist()
    leaked = [n for n in names if os.path.basename(n) in PERSONAL_FILES or n.endswith(".db")]
    if leaked:
        os.remove(src_zip_path)
        raise SystemExit(f"개인 데이터 파일이 소스 zip 에 포함되어 중단합니다: {leaked}")
    print(f"  + Source code archive created with {len(names)} files.")

    print("\n[Packaging Completed]")
    print(f"1. {exe_zip_name} ({os.path.getsize(exe_zip_path):,} bytes)")
    print(f"2. {src_zip_name} ({os.path.getsize(src_zip_path):,} bytes)")


if __name__ == "__main__":
    create_release_packages()
