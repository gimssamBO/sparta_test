@echo off
cd /d "%~dp0"
echo md 수정 자동 감시 서버를 시작합니다...
echo 이 창을 끈지 말고 있다가, 브라우저에서 http://127.0.0.1:8765 를 열어주세요.
echo.
where python >nul 2>nul
if %errorlevel%==0 (
    python watch_serve.py
) else (
    py watch_serve.py
)
pause
