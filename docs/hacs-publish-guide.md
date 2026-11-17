# HACS 发布指南

`petkit-feeder` 统一发布 Home Assistant 集成和 Lovelace 卡片。HACS 通过仓库根目录的 `hacs.json` 安装 `petkit_feeder.zip`。

## 发布新版

1. 有需要随 HACS 分发的集成或卡片改动时，更新 `custom_components/petkit_feeder/manifest.json` 中的 `version`。
2. 将改动合入 `main`。GitHub Actions 安装锁定的前端依赖、构建卡片，并运行 HACS 和 Hassfest 校验。
3. 校验通过后，CI 为新版创建 `vX.Y.Z` 标签并发布 ZIP。检查 [Releases](https://github.com/ningjx/petkit-feeder/releases) 中的 ZIP 包含 `manifest.json` 和 `www/petkit-feeder-card.js`。

维护者也可以推送与 `manifest.json` 版本对应的标签来发版。若标签创建后发布失败，可以复跑该 workflow，继续使用原标签和提交。

## HACS 安装和收录

- 在 HACS 的「自定义仓库」里添加 `https://github.com/ningjx/petkit-feeder`，类别选择「集成」。安装后重启 Home Assistant，再添加集成和卡片。详见 [安装说明](../README.md#安装)。
- HACS 默认收录入口为 `hacs/default` 的 `integration` 清单。主仓库的收录讨论在 [hacs/default#6766](https://github.com/hacs/default/pull/6766)。
