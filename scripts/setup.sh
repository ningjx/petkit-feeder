#!/bin/bash

#===============================================================================
# Petkit HA 部署脚本
# 用途：前端构建、后端部署、容器管理
#===============================================================================

set -e

#-------------------------------------------------------------------------------
# 颜色输出
#-------------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_step() { echo -e "${CYAN}🔹 $1${NC}"; }

#-------------------------------------------------------------------------------
# 配置
#-------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# HA 配置目录（可自定义）
HA_CONFIG_DIR="${HA_CONFIG_DIR:-/tmp/hass-config}"
CUSTOM_COMPONENTS_DIR="$HA_CONFIG_DIR/custom_components"
WWW_DIR="$HA_CONFIG_DIR/www"

# 容器名称
HA_CONTAINER_NAME="${HA_CONTAINER_NAME:-homeassistant}"

# 前端目录
CARD_DIR="$PROJECT_ROOT/petkit_feeder_card"
CARD_DIST_DIR="$CARD_DIR/dist"

#-------------------------------------------------------------------------------
# 帮助信息
#-------------------------------------------------------------------------------
show_help() {
    cat << EOF
🐾 Petkit HA 部署工具

用法：$0 [命令] [选项]

命令:
  all             完整部署（前端构建 + 后端部署 + 重启容器）
  frontend        仅前端：构建并复制卡片文件
  backend         仅后端：复制集成并重启容器
  build           仅构建前端（不复制）
  copy-card       仅复制前端卡片到 HA
  copy-plugin     仅复制后端插件到 HA
  restart         仅重启 HA 容器
  verify          验证 Python 语法
  clean           清理构建缓存
  status          显示当前状态

选项:
  -h, --help      显示帮助信息
  -n, --no-restart 不重启容器（用于 backend/all 命令）
  -f, --force     强制重新构建（清除缓存）
  -v, --verbose   显示详细信息

示例:
  $0 all                  # 完整部署
  $0 frontend             # 仅前端构建 + 复制
  $0 backend              # 仅后端部署 + 重启
  $0 build                # 仅构建前端
  $0 backend -n           # 后端部署但不重启
  $0 copy-card            # 仅复制前端卡片

环境变量:
  HA_CONFIG_DIR           HA 配置目录（默认：/tmp/hass-config）
  HA_CONTAINER_NAME       HA 容器名称（默认：homeassistant）

EOF
}

#-------------------------------------------------------------------------------
# 前端构建
#-------------------------------------------------------------------------------
build_frontend() {
    local force="${1:-false}"
    
    log_step "构建前端卡片..."
    
    if [ ! -d "$CARD_DIR" ]; then
        log_warning "petkit_feeder_card 目录不存在，跳过前端构建"
        return 0
    fi
    
    cd "$CARD_DIR"
    
    # 强制构建时清理
    if [ "$force" = "true" ]; then
        log_info "清理构建缓存..."
        rm -rf node_modules dist package-lock.json
    fi
    
    # 检测网络并设置镜像
    if ! ping -c 1 -W 2 github.com &> /dev/null; then
        npm config set registry https://registry.npmmirror.com
        log_info "使用淘宝 npm 镜像"
    fi
    
    # 安装依赖
    if [ ! -d "node_modules" ] || [ "$force" = "true" ]; then
        log_info "安装依赖..."
        npm install --legacy-peer-deps
    fi
    
    # 构建
    log_info "执行构建..."
    npm run build
    
    if [ -f "$CARD_DIST_DIR/petkit-feeder-card.js" ]; then
        local size=$(du -h "$CARD_DIST_DIR/petkit-feeder-card.js" | cut -f1)
        log_success "前端构建完成 ($size)"
        return 0
    else
        log_error "前端构建失败：找不到输出文件"
        return 1
    fi
}

#-------------------------------------------------------------------------------
# 复制前端卡片
#-------------------------------------------------------------------------------
copy_card() {
    log_step "复制前端卡片到 HA..."
    
    mkdir -p "$WWW_DIR"
    
    if [ ! -f "$CARD_DIST_DIR/petkit-feeder-card.js" ]; then
        log_error "前端卡片不存在，请先构建：$0 build"
        return 1
    fi
    
    cp "$CARD_DIST_DIR/petkit-feeder-card.js" "$WWW_DIR/" 2>/dev/null || \
    sudo cp "$CARD_DIST_DIR/petkit-feeder-card.js" "$WWW_DIR/"
    
    local size=$(du -h "$WWW_DIR/petkit-feeder-card.js" | cut -f1)
    log_success "前端卡片已复制到 $WWW_DIR ($size)"
    return 0
}

#-------------------------------------------------------------------------------
# 复制后端插件
#-------------------------------------------------------------------------------
copy_plugin() {
    log_step "复制后端插件到 HA..."
    
    local plugin_src="$PROJECT_ROOT/custom_components/petkit_feeder"
    
    if [ ! -d "$plugin_src" ]; then
        log_error "插件目录不存在：$plugin_src"
        return 1
    fi
    
    mkdir -p "$CUSTOM_COMPONENTS_DIR"
    
    # 删除旧版本（尝试 sudo）
    if [ -d "$CUSTOM_COMPONENTS_DIR/petkit_feeder" ]; then
        log_info "删除旧版本..."
        rm -rf "$CUSTOM_COMPONENTS_DIR/petkit_feeder" 2>/dev/null || \
        sudo rm -rf "$CUSTOM_COMPONENTS_DIR/petkit_feeder" 2>/dev/null || {
            log_warning "无法删除旧版本，尝试覆盖..."
        }
    fi
    
    # 复制新版本（尝试 sudo）
    cp -r "$plugin_src" "$CUSTOM_COMPONENTS_DIR/" 2>/dev/null || \
    sudo cp -r "$plugin_src" "$CUSTOM_COMPONENTS_DIR/"
    
    local file_count=$(find "$CUSTOM_COMPONENTS_DIR/petkit_feeder" -name "*.py" 2>/dev/null | wc -l)
    log_success "后端插件已复制到 $CUSTOM_COMPONENTS_DIR ($file_count 个 Python 文件)"
    return 0
}

#-------------------------------------------------------------------------------
# Python 语法检查
#-------------------------------------------------------------------------------
verify_python() {
    log_step "检查 Python 语法..."
    
    local plugin_dir="$PROJECT_ROOT/custom_components/petkit_feeder"
    local all_ok=true
    
    for file in "$plugin_dir"/*.py; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file" 2>/dev/null; then
                log_success "✓ $(basename $file)"
            else
                log_error "✗ $(basename $file) (语法错误)"
                all_ok=false
            fi
        fi
    done
    
    # 检查 pypetkitapi 目录
    if [ -d "$plugin_dir/pypetkitapi" ]; then
        for file in "$plugin_dir/pypetkitapi"/*.py; do
            if [ -f "$file" ]; then
                if python3 -m py_compile "$file" 2>/dev/null; then
                    log_success "✓ pypetkitapi/$(basename $file)"
                else
                    log_error "✗ pypetkitapi/$(basename $file) (语法错误)"
                    all_ok=false
                fi
            fi
        done
    fi
    
    if $all_ok; then
        log_success "Python 语法检查通过"
        return 0
    else
        log_error "Python 语法检查失败"
        return 1
    fi
}

#-------------------------------------------------------------------------------
# 重启 HA 容器
#-------------------------------------------------------------------------------
restart_ha() {
    log_step "重启 HA 容器..."
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${HA_CONTAINER_NAME}$"; then
        log_warning "容器 '${HA_CONTAINER_NAME}' 未运行"
        log_info "尝试启动容器..."
        docker start "${HA_CONTAINER_NAME}" 2>/dev/null || {
            log_error "无法启动容器，请检查 Docker 配置"
            return 1
        }
    fi
    
    docker restart "${HA_CONTAINER_NAME}"
    log_success "HA 容器已重启"
    
    log_info "等待 HA 启动..."
    sleep 5
    log_success "HA 应该已经可用 (http://localhost:8123)"
    return 0
}

#-------------------------------------------------------------------------------
# 创建 HA 容器（如果不存在）
#-------------------------------------------------------------------------------
create_ha_container() {
    log_step "检查 HA 容器..."
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${HA_CONTAINER_NAME}$"; then
        log_info "容器已存在，跳过创建"
        return 0
    fi
    
    log_info "容器不存在，开始创建..."
    
    # 创建必要的目录
    mkdir -p "$HA_CONFIG_DIR"
    
    # 拉取镜像
    log_info "拉取 Home Assistant 镜像..."
    docker pull ghcr.io/home-assistant/home-assistant:stable
    
    # 创建容器
    log_info "创建容器..."
    docker create \
        --name "${HA_CONTAINER_NAME}" \
        --privileged \
        --restart=unless-stopped \
        --network=host \
        -v "$HA_CONFIG_DIR:/config" \
        -v /run/dbus:/run/dbus:ro \
        ghcr.io/home-assistant/home-assistant:stable
    
    log_success "HA 容器创建成功"
    return 0
}

#-------------------------------------------------------------------------------
# 清理构建缓存
#-------------------------------------------------------------------------------
clean_cache() {
    log_step "清理构建缓存..."
    
    if [ -d "$CARD_DIR" ]; then
        cd "$CARD_DIR"
        log_info "清理前端缓存..."
        rm -rf node_modules dist package-lock.json
        log_success "前端缓存已清理"
    fi
    
    # 清理 Python 缓存
    find "$PROJECT_ROOT/custom_components" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT/custom_components" -name "*.pyc" -delete 2>/dev/null || true
    log_success "Python 缓存已清理"
    
    return 0
}

#-------------------------------------------------------------------------------
# 显示状态
#-------------------------------------------------------------------------------
show_status() {
    echo ""
    echo "==============================================================================="
    echo "📊 Petkit HA 状态"
    echo "==============================================================================="
    echo ""
    
    # 前端状态
    log_info "前端卡片:"
    if [ -f "$CARD_DIST_DIR/petkit-feeder-card.js" ]; then
        local size=$(du -h "$CARD_DIST_DIR/petkit-feeder-card.js" | cut -f1)
        local mtime=$(stat -c %y "$CARD_DIST_DIR/petkit-feeder-card.js" 2>/dev/null | cut -d. -f1)
        echo "  ✅ 已构建 ($size, $mtime)"
    else
        echo "  ❌ 未构建"
    fi
    
    # HA 配置目录
    log_info "HA 配置目录: $HA_CONFIG_DIR"
    if [ -d "$HA_CONFIG_DIR" ]; then
        echo "  ✅ 存在"
    else
        echo "  ❌ 不存在"
    fi
    
    # 后端插件
    if [ -d "$CUSTOM_COMPONENTS_DIR/petkit_feeder" ]; then
        local file_count=$(find "$CUSTOM_COMPONENTS_DIR/petkit_feeder" -name "*.py" | wc -l)
        echo "  ✅ 已部署 ($file_count 个 Python 文件)"
    else
        echo "  ❌ 未部署"
    fi
    
    # 前端卡片
    if [ -f "$WWW_DIR/petkit-feeder-card.js" ]; then
        local size=$(du -h "$WWW_DIR/petkit-feeder-card.js" | cut -f1)
        echo "  ✅ 前端卡片已复制 ($size)"
    else
        echo "  ❌ 前端卡片未复制"
    fi
    
    # HA 容器
    log_info "HA 容器:"
    if docker ps --format '{{.Names}}' | grep -q "^${HA_CONTAINER_NAME}$"; then
        local status=$(docker inspect -f '{{.State.Status}}' "${HA_CONTAINER_NAME}" 2>/dev/null)
        echo "  ✅ 运行中 ($status)"
    elif docker ps -a --format '{{.Names}}' | grep -q "^${HA_CONTAINER_NAME}$"; then
        echo "  ⚠️  已创建（未运行）"
    else
        echo "  ❌ 未创建"
    fi
    
    echo ""
    echo "==============================================================================="
    echo ""
}

#-------------------------------------------------------------------------------
# 完整部署
#-------------------------------------------------------------------------------
full_deploy() {
    local no_restart="${1:-false}"
    
    echo ""
    echo "==============================================================================="
    echo "🚀 完整部署 Petkit HA"
    echo "==============================================================================="
    echo ""
    
    # 步骤 1: 验证
    log_step "步骤 1/5: 验证 Python 语法"
    verify_python || exit 1
    echo ""
    
    # 步骤 2: 构建前端
    log_step "步骤 2/5: 构建前端卡片"
    build_frontend || exit 1
    echo ""
    
    # 步骤 3: 复制前端
    log_step "步骤 3/5: 复制前端卡片"
    copy_card || exit 1
    echo ""
    
    # 步骤 4: 复制后端
    log_step "步骤 4/5: 复制后端插件"
    copy_plugin || exit 1
    echo ""
    
    # 步骤 5: 重启容器
    if [ "$no_restart" = "false" ]; then
        log_step "步骤 5/5: 重启 HA 容器"
        restart_ha || exit 1
    else
        log_warning "跳过重启容器"
    fi
    
    echo ""
    echo "==============================================================================="
    echo "✅ 部署完成！"
    echo "==============================================================================="
    echo ""
    echo "下一步:"
    echo "  1. 浏览器访问 http://localhost:8123"
    echo "  2. 在 HA 中：设置 → 设备与服务 → 添加集成 → 搜索 '小佩'"
    echo "  3. 在 HA 中：控制面板 → 仪表板 → 添加卡片 → 搜索 'Petkit'"
    echo ""
}

#-------------------------------------------------------------------------------
# 主函数
#-------------------------------------------------------------------------------
main() {
    local command="${1:-help}"
    shift || true
    
    local no_restart="false"
    local force="false"
    local verbose="false"
    
    # 解析选项
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--no-restart)
                no_restart="true"
                shift
                ;;
            -f|--force)
                force="true"
                shift
                ;;
            -v|--verbose)
                verbose="true"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项：$1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 执行命令
    case "$command" in
        all)
            full_deploy "$no_restart"
            ;;
        frontend)
            build_frontend "$force"
            copy_card
            ;;
        backend)
            verify_python
            copy_plugin
            if [ "$no_restart" = "false" ]; then
                restart_ha
            fi
            ;;
        build)
            build_frontend "$force"
            ;;
        copy-card)
            copy_card
            ;;
        copy-plugin)
            copy_plugin
            ;;
        restart)
            restart_ha
            ;;
        verify)
            verify_python
            ;;
        clean)
            clean_cache
            ;;
        status)
            show_status
            ;;
        help|-h|--help)
            show_help
            ;;
        *)
            log_error "未知命令：$command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
