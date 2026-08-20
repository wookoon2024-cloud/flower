"""
[업무망 PC용] 오프라인 패키지 설치 스크립트 (Pure Python)
"""
import sys
import os
import subprocess

def install_offline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wheels_dir = os.path.join(base_dir, "wheels")

    packages = [
        "PySide6>=6.5.0",
        "requests>=2.28.0",
        "urllib3>=1.26.0",
        "Pillow>=9.0.0",
        "pyinstaller>=5.10.0"
    ]

    print("=== [1/2] 업무망 오프라인 패키지 설치 시작 ===")
    if not os.path.exists(wheels_dir):
        print(f"[오류] 'wheels' 폴더를 찾을 수 없습니다: {wheels_dir}")
        print("인터넷 PC에서 download_wheels.py를 실행하여 생성된 wheels 폴더를 함께 복사해 오세요.")
        return

    cmd = [sys.executable, "-m", "pip", "install", "--no-index", f"--find-links={wheels_dir}"] + packages
    print("Running:", " ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print("\n=== [2/2] 오프라인 패키지 설치 완료! ===")
        print("이제 'python build_exe.py'를 실행하여 업무망에서 EXE를 빌드하세요.")
    else:
        print(f"\n설치 실패: 반환 코드 {res.returncode}")

if __name__ == "__main__":
    install_offline()
