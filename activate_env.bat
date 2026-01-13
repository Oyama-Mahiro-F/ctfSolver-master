@echo off
REM CTF Solver 虚拟环境激活脚本 (Windows CMD)
REM 使用方法: activate_env.bat

echo 正在激活虚拟环境...
call venv\Scripts\activate.bat
echo 虚拟环境已激活！
echo.
echo 当前 Python 版本:
python --version
echo.
echo 提示: 使用 'deactivate' 命令退出虚拟环境
cmd /k
