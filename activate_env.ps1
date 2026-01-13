# CTF Solver 虚拟环境激活脚本
# 使用方法: .\activate_env.ps1

Write-Host "正在激活虚拟环境..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1
Write-Host "虚拟环境已激活！" -ForegroundColor Green
Write-Host ""
Write-Host "当前 Python 版本:" -ForegroundColor Yellow
python --version
Write-Host ""
Write-Host "提示: 使用 'deactivate' 命令退出虚拟环境" -ForegroundColor Cyan
