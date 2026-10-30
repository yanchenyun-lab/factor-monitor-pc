@echo off
chcp 65001 >nul
echo 正在启动 smartir-quant 量化服务...

if not defined APP_HOST set APP_HOST=0.0.0.0
if not defined APP_PORT set APP_PORT=8000
if not defined NACOS_SERVER_ADDR set NACOS_SERVER_ADDR=127.0.0.1:18848
if not defined SMARTIR_API_BASE set SMARTIR_API_BASE=http://127.0.0.1:8080

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

python main.py
pause

