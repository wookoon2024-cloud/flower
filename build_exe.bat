@echo off
chcp 65001 > nul
echo ========================================================
echo   🌿 [업무망 PC용] AI 반려화분 위젯 (마음지킴이) EXE 빌드
echo ========================================================
echo.

if exist "wheels" (
    echo [1/3] 오프라인 wheels 폴더에서 패키지 설치 확인...
    pip install --no-index --find-links=wheels/ -r requirements.txt
) else (
    echo [1/3] 필수 패키지 설치 확인...
    pip install -r requirements.txt
)

echo.
echo [2/3] PyInstaller 단일 실행 파일(.exe) 빌드 시작...
pyinstaller --clean --noconsole --onefile --name "AICompanionPlant" --icon "assets/app_icon.ico" --add-data "assets;assets" --add-data "config.json;." main.py

echo.
echo [3/3] 빌드 완료!
echo ========================================================
echo   ✅ 생성 완료 위치: dist\AICompanionPlant.exe
echo   이제 dist 폴더 안의 AICompanionPlant.exe 를 실행하시면 됩니다.
echo ========================================================
echo.
pause
