# D9 EPC Worldgen Fix

Minecraft 1.21.1 的服务端兼容补丁，针对 EPC 使用 `minecraft:lake` 水湖时触发的 MC-273228 / MC-272370。

错误表现：`LakeFeature.place` 调用群系查询，间接请求当前生成区域之外的区块，抛出 `IllegalStateException: Requested chunk unavailable during world generation`，可能让整台服务端退出。

## 范围

- 只重定向 `LakeFeature` 与 `SnowAndFreezeFeature` 的群系查询。
- 正常查询完全保留；仅对上述已知异常回退到不依赖已缓存区块的噪声群系查询。
- 回退将方块坐标转换为 quart 坐标，包括负坐标，避免在错误位置采样。
- 其他异常继续抛出，不全局吞掉世界生成错误。
- 不增加方块、物品或网络消息，只在服务端安装。数据包和客户端保持兼容。

问题背景参考 [WorldgenFeatureFix](https://modrinth.com/mod/worldgenfeaturefix)。D9 实现额外限制了异常范围，并使用正确的 quart 坐标。不要同时安装两个处理同一调用点的修复包。

## 构建和安装

需要 JDK 21。

```text
./gradlew build
```

将 `build/libs/epc-worldgen-fix-1.0.1-d9.1.jar` 放到 **服务端** `mods/` 后重启；数据包仍放在 `world/datapacks/`。当前以 NeoForge 21.1.248 / Youer f15a736d 验证，不要求客户端安装此补丁。

3 项测试覆盖正常路径、已知异常回退和负坐标换算、其他异常原样抛出。另在同版隔离服务端验证启动和 441 个区块实际生成。它修复这两个地物的已知查询问题，不承诺修复任意第三方世界生成错误。
