# Epic-Terrain

## D9：显式世界预设（Minecraft 1.21.1）

**安装数据包不会替换普通世界的地形。只有选择 `etn:epic_terrain` 世界预设，才使用 EPC。**

- 建筑主世界：首次创建前设置 `level-type=etn:epic_terrain`，并在初始启用列表中加入数据包。
- MV 资源世界：`mv create resource normal --seed <种子>`，使用原版生成配置。
- 下界、末地：使用原版定义。
- 仅需服务端数据包与服务端 MV；客户端不需要安装 EPC。

**Minecraft 1.21.1 还需服务端湖泊兼容补丁。** EPC 使用原版水湖地物，会触发 MC-273228/MC-272370 的生成边界查询崩溃。D9 修复源码与构建方法见 [服务端兼容补丁](compat/neoforge-1.21.1/README.md)，客户端不用安装。

版本：`0.1.4-d9.1`。构建：`python tools/build.py`，产物位于 `dist/`。

**[完整安装步骤、原理与服务端测试](docs/opt-in-world-preset.md)**

此分支的隔离实现位于 `versions/1.20.5-1.21.4/`，构建与验证仅面向 **1.21.1**。另外两个历史版本目录保留上游行为，不包含隔离修改。不要将原版 EPC 数据包与本版本同时安装。

已有 EPC 世界需要专门迁移；改 `level-type` 不会切换已有存档的生成器，也不能直接卸载仍被存档引用的数据包。

## 上游项目

高性能、写实的 Minecraft 地形重写数据包。厌倦了原版平坦乏味的地形？Epic-Terrain 重写了世界生成，带来山脉、阿尔卑斯式峰峦、大陆板块、侵蚀海岸线与全新的河流系统。

## 特性

- 平滑而真实的地表
- 壮观的阿尔卑斯式山峰
- 大陆板块式地形生成（海洋可绵延上万格）
- 全新海岸线：受侵蚀的峡湾、海、海峡、岛屿、半岛
- 新河流系统：大 / 小河、落差、源头

## 支持的 Minecraft 版本

| 数据包版本 | Minecraft 版本 | 说明 |
| --- | --- | --- |
| v0.2.5 (Beta) | 1.19.2 – 1.19.4 | 稳定 |
| v0.3.0 (Alpha) | 1.20 – 1.20.4 | 实验性 |
| v0.1.4 (Beta) | 1.20.5 – 1.21.4 | 稳定 |

> 1.19 理论上支持，但因 1.19 不支持自定义生物群系，作者不计划更新。

## 上游历史版本安装说明

1. 在 [Modrinth](https://modrinth.com/datapack/epicterrain) 下载对应你 MC 版本的数据包 `.zip`。
2. 放入存档目录 `saves/<世界>/datapacks/`，或客户端 `.minecraft/datapacks/`。
3. 进入世界后执行 `/reload`，或在创建世界时于「数据包」界面勾选启用。

以上为历史版本的上游说明。D9 的 1.21.1 构建请使用前文的显式预设安装步骤。

## 兼容性

- 实验性产品，**默认不考虑兼容性**；相关兼容修复见 companion 包 *Epic Terrain Compatible*。
- **Terrablender 不可用**：会禁用地表功能（如河流）。
- 生物群系分布已重置，几乎**不兼容**增加生物群系的模组；修改原版的模组可用。
- **已知 Bug（1.21+）**：`minecraft:lake` 在 1.21 有问题，请用修复模组 [worldgenfeaturefix](https://modrinth.com/mod/worldgenfeaturefix)。
- 地图尺寸极大（海洋可达 10000 格），建议配合 [World Preview](https://modrinth.com/mod/world-preview) 预览。

## 仓库结构

源码按 Minecraft 版本分目录存放于 `versions/`：

```
versions/
├── 1.19.2-1.19.4/   # v0.2.5 Beta
├── 1.20-1.20.4/     # v0.3.0 Alpha
└── 1.20.5-1.21.4/   # v0.1.4 Beta
```

每个目录都是一个**完整可打包的数据包**（`pack.mcmeta` + `data/`）。将其压缩为 `.zip` 即可作为数据包分发。配置文档见 `docs/`。

## 许可

MIT —— 见 [LICENSE](LICENSE)。

## 反馈

- Bug 报告：<https://github.com/wonderfulaichen/Epic-Terrain/issues>（兼容性问题请打 `Epic Terrain Compatible` 标签）
- 源代码：<https://github.com/wonderfulaichen/Epic-Terrain>
