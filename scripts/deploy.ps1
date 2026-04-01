#!/usr/bin/env pwsh
#Requires -Version 5.1

#===============================================================================
# Petkit HA 前端卡片构建脚本 (Windows)
# 用途：构建前端卡片
#===============================================================================

param(
    [switch]$Force,
    [switch]$Help
)

#-------------------------------------------------------------------------------
# 颜色输出函数
#-------------------------------------------------------------------------------
function Write-Info { param($Message) Write-Host "ℹ️  $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Step { param($Message) Write-Host "🔹 $Message" -ForegroundColor Cyan }

#-------------------------------------------------------------------------------
# 帮助信息
#-------------------------------------------------------------------------------
function Show-Help {
    $helpText = @"

🐾 Petkit HA 前端卡片构建工具 (Windows)

用法：.\deploy.ps1 [选项]

选项:
    -Force      强制重新构建（清除 node_modules 和 dist）
    -Help       显示帮助信息

示例:
    .\deploy.ps1              # 构建前端卡片
    .\deploy.ps1 -Force       # 强制重新构建

输出:
    构建产物位于: petkit_feeder_card\dist\

"@
    Write-Host $helpText
}

#-------------------------------------------------------------------------------
# 主构建函数
#-------------------------------------------------------------------------------
function Build-Frontend {
    param([bool]$Force = $false)
    
    Write-Step "构建前端卡片..."
    
    $scriptDir = $PSScriptRoot
    $projectRoot = Split-Path $scriptDir -Parent
    $cardDir = Join-Path $projectRoot "petkit_feeder_card"
    $distDir = Join-Path $cardDir "dist"
    
    # 检查目录是否存在
    if (-not (Test-Path $cardDir)) {
        Write-Warning "petkit_feeder_card 目录不存在，跳过前端构建"
        return $false
    }
    
    Push-Location $cardDir
    
    try {
        # 强制构建时清理
        if ($Force) {
            Write-Info "清理构建缓存..."
            if (Test-Path "node_modules") { Remove-Item -Recurse -Force "node_modules" }
            if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
            if (Test-Path "package-lock.json") { Remove-Item -Force "package-lock.json" }
        }
        
        # 检查 npm 是否可用
        $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
        if (-not $npmCmd) {
            Write-Error "未找到 npm，请先安装 Node.js"
            Write-Info "下载地址: https://nodejs.org/"
            return $false
        }
        
        # 安装依赖
        if (-not (Test-Path "node_modules") -or $Force) {
            Write-Info "安装依赖..."
            npm install --legacy-peer-deps
            if ($LASTEXITCODE -ne 0) {
                Write-Error "依赖安装失败"
                return $false
            }
        }
        
        # 构建
        Write-Info "执行构建..."
        npm run build
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "构建失败"
            return $false
        }
        
        # 验证输出
        $outputFile = Join-Path $distDir "petkit-feeder-card.js"
        if (Test-Path $outputFile) {
            $fileInfo = Get-Item $outputFile
            $sizeKB = [math]::Round($fileInfo.Length / 1KB, 2)
            Write-Success "前端构建完成 ($sizeKB KB)"
            Write-Info "输出目录: $distDir"
            return $true
        }
        else {
            Write-Error "前端构建失败：找不到输出文件"
            return $false
        }
    }
    finally {
        Pop-Location
    }
}

#-------------------------------------------------------------------------------
# 主程序
#-------------------------------------------------------------------------------
if ($Help) {
    Show-Help
    exit 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🐾 Petkit HA 前端卡片构建工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$success = Build-Frontend -Force:$Force

Write-Host ""
if ($success) {
    Write-Success "构建成功！"
    exit 0
}
else {
    Write-Error "构建失败！"
    exit 1
}