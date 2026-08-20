@echo off
chcp 65001 > nul
echo ========================================================
echo   🌿 AI 반려화분 위젯 (마음지킴이) EXE 단일 실행파일 빌드
echo ========================================================
echo.

echo [1/3] 필수 패키지 설치 확인...
pip install -r requirements.txt

echo.
echo [2/3] PyInstaller 단일 실행 파일(.exe) 빌드 시작...
pyinstaller --clean --noconsole --onefile --name "AICompanionPlant" --icon "assets/app_icon.ico" --add-data "assets;assets" --add-data "config.json;." main.py

echo.
echo [3/3] 빌드 완료!
echo ========================================================
echo   ✅ 생성 완료 위치: dist\AICompanionPlant.exe
echo   업무망에는 dist\AICompanionPlant.exe 파일 하나만 복사하시면 됩니다.
echo ========================================================
echo.
pause
