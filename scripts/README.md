# Petkit HA 部署脚本

🫡 一站式部署工具 - 前端构建、后端部署、容器管理

---

## 🚀 快速开始

### 完整部署（一键部署）

```bash
./scripts/setup.sh all
```

### 仅部署前端

```bash
./scripts/setup.sh frontend
```

### 仅部署后端

```bash
./scripts/setup.sh backend
```

---

## 📋 命令列表

| 命令 | 说明 |
|------|------|
| `all` | 完整部署（前端构建 + 后端部署 + 重启容器） |
| `frontend` | 仅前端：构建并复制卡片文件 |
| `backend` | 仅后端：复制集成并重启容器 |
| `build` | 仅构建前端（不复制） |
| `copy-card` | 仅复制前端卡片到 HA |
| `copy-plugin` | 仅复制后端插件到 HA |
| `restart` | 仅重启 HA 容器 |
| `verify` | 验证 Python 语法 |
| `clean` | 清理构建缓存 |
| `status` | 显示当前状态 |
| `help` | 显示帮助信息 |

---

## 🔧 选项

| 选项 | 说明 | 适用命令 |
|------|------|---------|
| `-h, --help` | 显示帮助信息 | 所有 |
| `-n, --no-restart` | 不重启容器 | `all`, `backend` |
| `-f, --force` | 强制重新构建（清除缓存） | `build`, `frontend`, `all` |
| `-v, --verbose` | 显示详细信息 | 所有 |

---

## 💡 使用示例

### 1. 完整部署

```bash
# 完整部署（前端 + 后端 + 重启）
./scripts/setup.sh all

# 完整部署但不重启容器
./scripts/setup.sh all -n
```

### 2. 仅更新前端

```bash
# 构建并复制前端卡片
./scripts/setup.sh frontend

# 仅构建（测试用）
./scripts/setup.sh build

# 仅复制（快速更新）
./scripts/setup.sh copy-card
```

### 3. 仅更新后端

```bash
# 部署后端并重启
./scripts/setup.sh backend

# 部署后端但不重启
./scripts/setup.sh backend -n

# 仅复制插件
./scripts/setup.sh copy-plugin
```

### 4. 开发调试

```bash
# 强制重新构建（清理缓存）
./scripts/setup.sh build -f

# 检查 Python 语法
./scripts/setup.sh verify

# 查看当前状态
./scripts/setup.sh status

# 清理缓存
./scripts/setup.sh clean
```

### 5. 容器管理

```bash
# 重启 HA 容器
./scripts/setup.sh restart
```

---

## 🌍 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `HA_CONFIG_DIR` | `/tmp/hass-config` | HA 配置目录 |
| `HA_CONTAINER_NAME` | `homeassistant` | HA 容器名称 |

### 使用示例

```bash
# 自定义 HA 配置目录
HA_CONFIG_DIR=/home/user/hass-config ./scripts/setup.sh all

# 自定义容器名称
HA_CONTAINER_NAME=my-hass ./scripts/setup.sh restart

# 同时设置多个
HA_CONFIG_DIR=/opt/hass HA_CONTAINER_NAME=ha-test ./scripts/setup.sh backend
```

---

## 📊 输出示例

### 状态查看

```bash
$ ./scripts/setup.sh status

===============================================================================
📊 Petkit HA 状态
===============================================================================

ℹ️  前端卡片:
  ✅ 已构建 (32K, 2026-03-12 16:27:45)
ℹ️  HA 配置目录：/tmp/hass-config
  ✅ 存在
  ✅ 已部署 (23 个 Python 文件)
  ✅ 前端卡片已复制 (32K)
ℹ️  HA 容器:
  ✅ 运行中 (running)

===============================================================================
```

### Python 语法检查

```bash
$ ./scripts/setup.sh verify

🔹 检查 Python 语法...
✅ ✓ binary_sensor.py
✅ ✓ button.py
✅ ✓ config_flow.py
✅ ✓ const.py
✅ ✓ coordinator.py
✅ ✓ __init__.py
✅ ✓ number.py
✅ ✓ sensor.py
✅ ✓ switch.py
✅ ✓ pypetkitapi/bluetooth.py
✅ ✓ pypetkitapi/client.py
...
✅ Python 语法检查通过
```

### 前端构建

```bash
$ ./scripts/setup.sh build

🔹 构建前端卡片...
ℹ️  执行构建...

> petkit-feeder-card@0.3.0 build
> rollup -c --bundleConfigAsCjs

created dist/petkit-feeder-card.js in 3.9s
✅ 前端构建完成 (32K)
```

---

## 🔐 权限说明

脚本会自动尝试使用 `sudo` 提升权限（如果需要）。

如果遇到权限错误，可以：

### 方式 1: 使用 sudo 运行脚本

```bash
sudo ./scripts/setup.sh all
```

### 方式 2: 修改 HA 配置目录权限

```bash
sudo chown -R $USER:$USER /tmp/hass-config
```

### 方式 3: 使用用户目录

```bash
HA_CONFIG_DIR=$HOME/hass-config ./scripts/setup.sh all
```

---

## 🛠️ 故障排查

### 问题 1: 前端构建失败

```bash
# 清理缓存后重试
./scripts/setup.sh build -f

# 检查 node 版本
node --version  # 需要 >= 18

# 检查 npm 版本
npm --version  # 需要 >= 9
```

### 问题 2: Python 语法检查失败

```bash
# 查看详细错误
python3 -m py_compile custom_components/petkit_feeder/<文件>.py

# 修复后重新检查
./scripts/setup.sh verify
```

### 问题 3: 容器无法重启

```bash
# 检查 Docker 权限
docker ps

# 手动重启容器
docker restart homeassistant

# 检查容器状态
docker ps -a | grep homeassistant
```

### 问题 4: 文件复制失败

```bash
# 检查目标目录权限
ls -la /tmp/hass-config/

# 使用 sudo 复制
sudo ./scripts/setup.sh copy-plugin

# 或修改目录权限
sudo chown -R $USER:$USER /tmp/hass-config/
```

---

## 📁 目录结构

```
petkit-ha/
├── scripts/
│   ├── setup.sh          # 主部署脚本
│   ├── README.md         # 脚本说明（本文件）
│   └── check_code.py     # 代码检查工具
├── petkit_feeder_card/   # 前端卡片
│   ├── src/
│   ├── dist/
│   └── package.json
├── custom_components/    # 后端插件
│   └── petkit_feeder/
└── ...
```

---

## 🎯 最佳实践

### 开发流程

```bash
# 1. 修改前端代码
cd card && npm run start  # 监听模式

# 2. 修改后端代码
# ... 编辑 Python 文件 ...

# 3. 验证 Python 语法
./scripts/setup.sh verify

# 4. 构建前端
./scripts/setup.sh build

# 5. 复制文件
./scripts/setup.sh copy-card
./scripts/setup.sh copy-plugin

# 6. 重启 HA
./scripts/setup.sh restart
```

### 生产部署

```bash
# 一键完整部署
./scripts/setup.sh all

# 或分步部署（更可控）
./scripts/setup.sh verify      # 验证
./scripts/setup.sh frontend    # 前端
./scripts/setup.sh backend -n  # 后端（不重启）

# 测试无误后重启
./scripts/setup.sh restart
```

---

## 📝 更新日志

### v2.0 (2026-03-12)

**完全重写**

- ✨ 新增命令分离前端和后端
- ✨ 新增选项支持（-n, -f, -v）
- ✨ 新增状态查看功能
- ✨ 新增环境变量支持
- 🎨 改进输出格式和颜色
- 🔧 支持 sudo 权限提升
- 📊 改进 Python 语法检查

### v1.0 (2026-03-09)

- 🎉 初始版本

---

**Made with ❤️ by 甘 🫡**
