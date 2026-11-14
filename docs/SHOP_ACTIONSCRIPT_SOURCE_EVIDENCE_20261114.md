# 魔塔 1.12 商店原版 ActionScript 取证（2026-11-14）

> 来源：`game.swf` SHA-256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`；GitHub Actions [SWF Audit #43603442337](https://github.com/mjw3177109/motafukepygame/actions/runs/43603442337)，[Artifact #14116789420](https://github.com/mjw3177109/motafukepygame/actions/runs/43603442337/artifacts/14116789420)。两份 FFDec 独立导出的字节内容已对比相同。以下仅为反编译源码可见的静态分支，不代表 Flash 运行时或双端行为验收。

## 原版取证锚点

| 文件 | 字节数 | SHA-256 |
| --- | ---: | --- |
| `scripts/DefineSprite_671_mt_buy/frame_2/DoAction.as` | 1205 | `084e459b77dba8a44c9643669ae48394964b8e278fe44ff282998c3468092b3e` |
| `scripts/DefineSprite_671_mt_buy/frame_4/DoAction.as` | 1387 | `56c0d0f39984abc6651a8346b7c24c6e85da678d54d7875fe91cef4b18455405` |

## frame_2 — `Case_buy_01()`

- 初始 `now_case_id = 1`，`stop()`。
- 当 `Now_money >= 25`：选项 1 扣 25 金币并增加 800 HP；选项 2 扣 25 金币并增加 4 攻击；选项 3 扣 25 金币并增加 4 防御。成功时更新对应 `mt_Mylife` 展示字段及金币字段，并播放 `music_11`。
- 选项 4：金币是否达到 25 均可退出；播放 `music_07`，`gotoAndPlay("end")`。
- 金币不足且选项非 4：播放 `music_09`；源码未显示扣费或属性增量。
- 注意：金币充足但 `now_case_id` 不在 1–4 时，`switch` 无匹配分支；不得假设会播放失败音效。

## frame_4 — `Case_buy_03()`

- 初始 `now_case_id = 1`，`stop()`。
- 选项 1：黄色钥匙，金币至少 10，扣 10、`Now_yellow += 1`，同步 `mt_Mykey.Key_yellow` 和展示金币。
- 选项 2：蓝色钥匙，金币至少 50，扣 50、`Now_blue += 1`，同步 `mt_Mykey.Key_blue` 和展示金币。
- 选项 3：红色钥匙，金币至少 100，扣 100、`Now_red += 1`，同步 `mt_Mykey.Key_red` 和展示金币。
- 购买成功播放 `music_11`；余额不足播放 `music_09`，源码未显示扣费或加钥匙。
- 选项 4：无余额条件，播放 `music_07`，`gotoAndStop("end")`。注意与 frame_2 的 `gotoAndPlay` 不同。
- 未匹配选项：源码未显示状态改变或音效。

## 下一步可执行回归用例（待实现，不能标为通过）

1. 对两帧每个有效购买选项测试金币恰好等于价格、少 1、超过价格三种初始状态，断言金币、HP/攻/防/钥匙及 UI 展示字段。
2. 测试两帧选项 4 在余额为 0 时都可退出，并分别核对 `gotoAndPlay` / `gotoAndStop`。
3. 测试非法选项和余额不足时无意外状态变化；检查音效调用。
4. 将以上结果与原版 Flash 实际操作录屏/状态轨迹、Pygame、HTML5 三方对照。当前**尚未**获得这些运行时证据。

## 门禁

`ActionRecord` 字节级验证、原版运行时行为、Pygame/HTML5 状态一致性、地图/结局人工验收均未完成。不得凭本静态文档宣称 1:1 或启动 Gymnasium/Kaggle 训练。
