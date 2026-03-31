# PetKit 喂食器 Home Assistant 集成

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant 原生集成，支持小佩智能喂食器的完整功能控制。

## 功能特性

- 喂食计划管理 - 新增/删除/修改计划，自动同步一周
- 喂食历史记录 - 追踪每次喂食详情
- 手动喂食 - 一键出粮
- 状态监控 - 在线状态、WiFi 信号、干燥剂状态
- 美观卡片 - 专为 Lovelace 设计的可视化界面
- 多设备支持 - 通过设备 ID 区分不同设备

## 安装

### HACS 安装（推荐）

1. HACS → 集成 → 探索并下载仓库
2. 搜索 "Petkit Feeder"
3. 点击下载并重启 Home Assistant
4. 设置 → 设备与服务 → 添加集成 → 搜索 "Petkit"

### 手动安装

```bash
cd /config/custom_components
git clone https://github.com/yourusername/petkit-ha.git petkit_feeder
```

重启 Home Assistant 后添加集成。

## 配置

通过 UI 配置：设置 → 设备与服务 → 添加集成 → Petkit

输入小佩账号（手机号 + 密码），选择设备。

## 实体

实体 ID 格式：`{type}.petkit_feeder_{device_id}_{name}`

| 实体 | 类型 | 说明 |
|------|------|------|
| `sensor.petkit_feeder_{id}_feeding_schedule` | sensor | 喂食计划（周一到周日） |
| `sensor.petkit_feeder_{id}_feeding_history` | sensor | 喂食历史记录 |
| `sensor.petkit_feeder_{id}_device_name` | sensor | 设备名称 |
| `sensor.petkit_feeder_{id}_device_id` | sensor | 设备ID |
| `sensor.petkit_feeder_{id}_last_feeding` | sensor | 最后喂食时间 |
| `sensor.petkit_feeder_{id}_last_amount` | sensor | 最后喂食量 |
| `sensor.petkit_feeder_{id}_today_count` | sensor | 今日喂食次数 |
| `binary_sensor.petkit_feeder_{id}_online` | binary_sensor | 在线状态 |
| `button.petkit_feeder_{id}_feed` | button | 手动喂食 |
| `button.petkit_feeder_{id}_refresh` | button | 刷新数据 |
| `switch.petkit_feeder_{id}_manual_lock` | switch | 手动出粮锁定 |
| `number.petkit_feeder_{id}_feed_amount` | number | 默认出粮量 |

## 服务

| 服务 | 说明 |
|------|------|
| `petkit_feeder.add_feeding_item` | 新增计划（同步一周） |
| `petkit_feeder.remove_feeding_item` | 删除计划（同步一周） |
| `petkit_feeder.update_feeding_item` | 修改计划（同步一周） |
| `petkit_feeder.toggle_feeding_item` | 启用/禁用计划 |

### 示例

```yaml
# 新增计划（自动同步到一周 7 天）
service: petkit_feeder.add_feeding_item
data:
  day: 1
  time: "08:00"
  amount: 10
  name: "早餐"

# 删除计划
service: petkit_feeder.remove_feeding_item
data:
  day: 1
  item_id: "28800"  # 时间秒数

# 修改计划
service: petkit_feeder.update_feeding_item
data:
  day: 1
  item_id: "28800"
  time: "08:30"
  amount: 15
```

## Lovelace 卡片

```yaml
type: custom:petkit-feeder-card
device_id: "276669"
show_timeline: true
show_summary: true
show_actions: true
```

### 卡片功能

- 今日时间线 - 显示计划和执行记录
- 计划管理 - 点击时间/名称/克数编辑，点击删除按钮删除
- 新增计划 - 点击底部虚线框添加新计划
- 乐观更新 - 操作立即生效，后台异步同步
- 状态同步 - 修改一天的计划自动同步一周
- 多设备 - 通过 device_id 绑定特定设备

## 开发

```bash
# 安装依赖
cd card && npm install

# 开发模式
npm run dev

# 构建
npm run build
```

## 注意事项

- 本项目非小佩官方产品
- API 可能随时变更
- 账号信息由 Home Assistant 加密存储

## 许可证

MIT License