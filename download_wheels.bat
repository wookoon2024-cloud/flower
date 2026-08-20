@echo off
chcp 65001 > nul
echo ========================================================
echo   [인터넷 PC용] 업무망 오프라인 패키지(Wheels) 다운로더
echo ========================================================
echo.
echo [1/2] wheels 폴더 생성 및 오프라인 패키지 다운로드 중...
if not exist "wheels" mkdir wheels

pip download -r requirements.txt -d wheels/

echo.
echo ========================================================
echo   ✅ 다운로드 완료!
echo   'wheels' 폴더를 소스 코드와 함께 업무망으로 복사하세요.
echo ========================================================
echo.
pause
