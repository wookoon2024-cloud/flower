"""
[인터넷 PC용] 오프라인 패키지 다운로드 스크립트 (Pure Python)
"""
import sys
import os
import subprocess

def download_wheels():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wheels_dir = os.path.join(base_dir, "wheels")
    os.makedirs(wheels_dir, exist_ok=True)

    packages = [
        "PySide6>=6.5.0",
        "requests>=2.28.0",
        "urllib3>=1.26.0",
        "Pillow>=9.0.0",
        "pyinstaller>=5.10.0"
    ]

    print("=== [1/2] 업무망 오프라인용 Wheel 패키지 다운로드 시작 ===")
    cmd = [sys.executable, "-m", "pip", "download"] + packages + ["-d", wheels_dir]
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print("\n=== [2/2] 다운로드 성공! ===")
        print(f"생성된 'wheels' 폴더 ({wheels_dir})를 .py 파일들과 함께 업무망으로 복사하세요.")
    else:
        print(f"\n다운로드 실패: 반환 코드 {res.returncode}")

if __name__ == "__main__":
    download_wheels()
