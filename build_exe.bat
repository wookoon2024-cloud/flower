@echo off
chcp 65001 > nul
echo ===================================================
echo [AI 반려화분] Windows 독립 실행 파일(.exe) 빌드 시작
echo ===================================================
python build_exe.py
echo.
echo 빌드가 완료되었습니다. dist\AICompanionPlant.exe 를 확인하세요.
pause
