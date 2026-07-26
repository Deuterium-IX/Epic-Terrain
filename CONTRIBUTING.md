# 贡献指南

感谢你对 Epic-Terrain 感兴趣。

## 报告问题

- 在 [Issues](https://github.com/wonderfulaichen/Epic-Terrain/issues) 提交 Bug。
- **兼容性问题请打 `Epic Terrain Compatible` 标签**，便于分类。
- 提交时请注明：Minecraft 版本、数据包版本、加载器（原版 / Forge / NeoForge / Fabric / Quilt）、复现步骤。

## 仓库约定

- 本仓库以**数据包源码**为主，每个 Minecraft 版本源码位于 `versions/<mc-range>/`。
- 每个版本目录都是完整可打包的数据包（`pack.mcmeta` + `data/`），修改请只改动对应目录。
- 新增 Minecraft 版本时，新建 `versions/<mc-range>/` 并放入对应源码。
- 配置文档统一放在 `docs/`。

## 提交信息

简洁说明改动，例如：

- `fix: 修正 1.21 河流生成偏移`
- `feat: 1.20.5-1.21.4 新增峡湾海岸线`
- `docs: 补全 README 版本矩阵`

## 许可

所有贡献均遵循仓库 [LICENSE](LICENSE)（MIT）。
