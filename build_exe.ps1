# ─── Gnirehtet GUI 打包脚本 ───────────────────────────────────
# 运行方式：右键 → 用 PowerShell 运行，或在终端执行 .\build_exe.ps1

Set-Location $PSScriptRoot

Write-Host ">>> 安装 / 更新 PyInstaller 和 Pillow..." -ForegroundColor Cyan
pip install pyinstaller pillow -q

# 将 icon.png 转换为 icon.ico（PyInstaller 在 Windows 上需要 .ico）
if (Test-Path "icon.png") {
    Write-Host ">>> 将 icon.png 转换为 icon.ico..." -ForegroundColor Cyan
    python -c "
from PIL import Image
img = Image.open('icon.png').convert('RGBA')
img.save('icon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('icon.ico 生成成功')
"
} else {
    Write-Host ">>> 未找到 icon.png，将使用默认图标" -ForegroundColor Yellow
}

Write-Host ">>> 开始打包..." -ForegroundColor Cyan

$iconArg = if (Test-Path "icon.ico") { "--icon"; "icon.ico" } else { @() }

python -m PyInstaller `
    --onefile `
    --windowed `
    --name "GnirehtetGUI" `
    @iconArg `
    --add-binary "gnirehtet.exe;." `
    --add-binary "gnirehtet.apk;." `
    --add-binary "adb.exe;." `
    --add-binary "AdbWinApi.dll;." `
    --add-binary "AdbWinUsbApi.dll;." `
    --add-binary "libwinpthread-1.dll;." `
    --add-data "icon.png;." `
    --collect-all PySide6 `
    gnirehtet_gui.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host ">>> 打包成功！输出文件：" -ForegroundColor Green
    Write-Host "    $PSScriptRoot\dist\GnirehtetGUI.exe" -ForegroundColor Green
    Write-Host ""
    Write-Host ">>> 清理临时文件..." -ForegroundColor DarkGray
    Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
    Remove-Item -Force GnirehtetGUI.spec -ErrorAction SilentlyContinue
    Remove-Item -Force icon.ico -ErrorAction SilentlyContinue
} else {
    Write-Host ">>> 打包失败，请查看上方错误信息" -ForegroundColor Red
}
