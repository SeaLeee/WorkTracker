@echo off
chcp 65001 >nul
echo ================================
echo   工作需求记录管理系统
echo ================================
echo.

cd /d "%~dp0"

echo 正在检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo 正在检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

echo.
echo 正在启动服务器...
echo 请在浏览器中访问: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo.

:: 延迟2秒后自动打开浏览器
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

python app.py
