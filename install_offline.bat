@echo off
chcp 65001 > nul
echo ========================================================
echo   [업무망 PC용] 오프라인 패키지 설치 (망분리/인터넷 차단 환경)
echo ========================================================
echo.

if not exist "wheels" (
    echo [오류] 'wheels' 폴더가 없습니다. 
    echo 인터넷 PC에서 download_wheels.bat을 실행하여 생성된 wheels 폴더를 복사해오세요.
    pause
    exit /b
)

echo [1/2] 오프라인 패키지 설치 중...
pip install --no-index --find-links=wheels/ -r requirements.txt

echo.
echo ========================================================
echo   ✅ 오프라인 패키지 설치 완료!
echo   이제 build_exe.bat 을 실행하여 업무망에서 EXE를 빌드하세요.
echo ========================================================
echo.
pause
