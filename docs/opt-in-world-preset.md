# D9：按世界预设启用 Epic Terrain

## 行为

此修改面向 Minecraft Java 1.21.1 的服务端。`etn:epic_terrain` 是显式选择的世界预设。

| 创建方式 | 主世界地形 |
| --- | --- |
| 不安装数据包，普通预设 | 原版 |
| 安装数据包，普通预设 | 原版 |
| 安装数据包，选择 `etn:epic_terrain` | Epic Terrain |
| 在该服务端执行 `mv create resource normal` | 原版资源世界 |

EPC 的逻辑来自服务端数据包，不需要客户端安装 EPC，也不需要客户端安装 MV。

## 新建 EPC 建筑主世界

下面是 Youer / NeoForge 服务端的首次创建配置。请使用全新的世界目录；已有 `level.dat` 时仅改 `level-type` 不会替换存档的生成器。

1. 把构建得到的 ZIP 放到 `world/datapacks/`。
2. 在首次启动前设置 `server.properties`：

```properties
level-name=world
level-seed=246813579
level-type=etn:epic_terrain
initial-enabled-packs=vanilla,mod_data,file/epic-terrain-0.1.4-d9.1-mc1.21.1.zip
```

`file/` 后必须与实际 ZIP 文件名完全一致。`mod_data` 是 NeoForge/Youer 的数据包；原版服务端配置不包含它。保留你的其他必要初始数据包。

3. 启动后检查 `datapack list enabled`，确认 EPC 数据包已启用。
4. 如果使用 MV，创建普通资源世界：

```text
mv create resource normal --seed 246813579
```

可以指定其他种子。`normal` 选择原版世界预设，不需要 EPC 生成器插件，也不要向 `resource/datapacks` 放另一份 EPC。

### 使用普通建筑主世界

将 `level-type` 设为 `minecraft:normal` 即可。数据包即使已经启用，也不会主动替换普通世界的地形。

## 为什么能够隔离

- 原 `data/minecraft/dimension/overworld.json` 被改为 `data/etn/worldgen/world_preset/epic_terrain.json` 内的显式主世界定义。数据包不自动注册任何维度。
- 原版命名空间中的维度类型、生成设置、噪声、密度函数和两个沼泽群系已移至 `etn:epic/*`。
- EPC 引用它们的位置同步改为专属 ID。原版方块、codec 类型以及 `effects: minecraft:overworld` 等标识保持原样。
- 四个需要继承原 EPC 覆盖效果的原版密度函数被复制到 `etn:vanilla/*`：`shift_x`、`shift_z`、`overworld/factor`、`overworld/ridges_folded`。其余原版函数继续共享。
- `data/minecraft/` 只保留 `replace: false` 的标签追加：将预设加入可选列表，并让 EPC 自有沼泽群系继承相应原版群系标签。没有替换原版定义、标签成员或默认预设。
- EPC 预设中的下界和末地继续引用原版定义。

MV 和 Youer 仍共享注册表；隔离来自 EPC 不再覆盖普通世界使用的资源，不依赖修改 MV。

## 使用范围与存档限制

- 本次构建和服务端验证目标为 **Minecraft 1.21.1**。源码暂保留上游目录名 `1.20.5-1.21.4`，不以该目录名承诺整个版本区间都经过验证。
- `versions/1.19.2-1.19.4` 和 `versions/1.20-1.20.4` 是上游历史实现，仍采用旧的全局覆盖方式，不属于此构建。
- 这是新世界方案，不自动迁移原版 EPC 存档。噪声资源 ID 改变后，同种子的地形可能不同；不要在已有地图中直接替换原包继续生成新区块。
- 使用了 EPC 群系、维度类型或生成器配置的世界仍依赖此数据包。显式启用不等于可随意卸载。
- 第三方数据包仍可能自行覆盖原版资源。例如 Amiya 现有的 WorldPainter 高度包需要单独处理；本修改保证 EPC 自身不覆盖原版，不替其他数据包恢复原版配置。
- 没有修改 EPC 的地形权重、山脉或河流设计。本改动仅解决启用方式与世界间的配置隔离。
- 服务端测试还修正了上游湖泊数量提供器的旧 JSON 格式：`biased_to_bottom` 的上下限直接放在对象内，去掉旧的 `value` 包装。数值与权重保持不变；旧格式会阻止 1.21.1 加载数据包。

## 构建与检查

```text
python -m unittest discover -s tests -v
python tools/build.py
```

产物在 `dist/`，ZIP 包含 MIT 许可证，并附 SHA-256 校验文件。构建不需要 Java、Gradle或客户端。

### 服务端冒烟测试

`tools/smoke_server.py` 会创建三个全新服务端实例，各启动两次。模板仅提供 `youer.jar`、`libraries/` 和已经接受的 `eula.txt`，不复制世界、玩家或业务配置。它只使用本地回环地址，输出位于仓库 `build/`。

安装 Python 的 `nbtlib`，并准备 Java 21、Youer 运行目录、MV 和 YourFix JAR 后执行：

```text
python tools/smoke_server.py --template <runtime-directory> --mv-jar <multiverse.jar> --yourfix-jar <yourfix.jar> --java <java-executable>
```

三组环境分别为：无 EPC、EPC 已安装但选择普通预设、EPC 已安装且选择 EPC 预设。每组均用 MV 创建同种子的普通资源世界，并在初次启动和重启后分别生成新的样本区块。脚本校验：

- 各组资源世界的 `OCEAN_FLOOR` 高度图与逐位置解码的群系哈希相同；
- 安装 EPC 但不选择时，普通主世界与无 EPC 基线相同；
- 选择 EPC 时，主世界引用 EPC 专属维度类型与生成设置，且地形不同；
- 新建和重启后继续生成区块成功。

样本检查不代表全地图逐区块验证，也不包含其他模组组合或存档迁移。

完整方块 NBT 哈希保留为诊断信息，不作为一致性断言：重复运行不安装 EPC 的相同基线时，也观察到少量矿石与草木摆放差异。因此通过结果证明的是样本高度图、群系与生成配置一致，不声称所有装饰或每个方块逐位相同。已停止的测试存档可用 `python tools/smoke_server.py --verify-only build/<run-directory>` 重新核验。

测试发现：原版 MV 5.8.1 在 Youer `f15a736d` 上会因默认世界重命名/末地重复登记，抛出 `WorldConfig for world minecraft:the_end already exists`，中断额外世界自动加载；不安装 EPC 的基线也有此问题。冒烟测试在三组环境中统一关闭 `world.auto-import-default-worlds` 与 `world.auto-import-3rd-party-worlds`，保留已登记资源世界的自动加载，以隔离 EPC 的影响。此设置只写入测试目录，不修改正式服。生产若遇到相同错误，需单独处理 MV 的导入配置或使用已有兼容修复；该问题不是 EPC 能从数据包内修复的。
