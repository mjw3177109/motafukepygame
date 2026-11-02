# 原版第八组对话状态交接源码审计

本增量从原始 `game.swf` 的 FFDec 导出取证，依托已有 `audit_terminal_candidates` 对 SWF SHA256、完整 ActionScript 清单、逐文件大小和 SHA256 进行校验，再核对四份指定脚本的局部语句。**仅核对源码文本锚点，不运行 Flash，也不推断帧执行顺序。**

| 源码位置 | 可核对的文本状态 |
| --- | --- |
| `DefineSprite_795_mt_say_08/frame_6` | `Display_say[8] = 2` |
| `DefineSprite_795_mt_say_08/frame_9` | `Display_say[8] = 5` |
| `DefineSprite_795_mt_say_08/frame_12` | `Display_say[8] = 9` |
| `DefineSprite_855/frame_1` | 文字条件 `2→3`、`5→6`、`9→10`，并在 `9` 分支出现 `mt_LastGame_ID == 0` 的 `game_over` 跳转及 `== 1` 的后续分支 |

使用方法：

```bash
python -m tools.audit_say08_handoff --manifest .swf_audit/manifest.json --export-root .swf_audit/export --swf game.swf --out .swf_audit/original_say08_handoff.json
```

输出每个锚点的脚本 SHA256、行号和静态匹配结果；原版实机执行、结局语义、Pygame/HTML5 一致性、Gymnasium 和 Kaggle 全部继续标记为未验收。若 FFDec 漂移导致目标语句改变，审计失败并保留 CI 日志，不能通过修改预期值绕过来源核验。

下一步需获取真实 Flash 操作轨迹和第八组对话的帧推进条件，再据此设计双端状态机及回归。原版 Flash 截图基准、`mt_06` 差异及完整结局仍是独立阻碍。

## 本轮增量：结局分支状态来源索引

审计报告 schema 升级到 v2，新增 `terminal_guard`，从已通过原始 SWF SHA256、完整 FFDec 脚本清单与逐文件字节哈希校验的候选索引中，单独列出 `mt_LastGame_ID` 的写入**文本候选**。每项包含源文件、行列、运算符、源码 SHA256 和相邻源码窗口。这样可以优先检查 `mt_LastGame_ID == 0/1` 的上游状态来源，而不必从 105 处混合状态写入候选中手工筛选。

回归覆盖同一变量的普通赋值、复合赋值、条件比较排除、来源哈希及零候选情形。输出的 `runtime_value_proven=false` 明确表示：即使发现赋值语句，也**不能证明**该赋值在真实 Flash 游戏里执行过、其执行先后、默认值或结局是否正确。原有文本候选索引不是 ActionScript 语法树，注释或字符串仍可能被检出，需对候选逐条复核上下文。

本轮未修改 Pygame/HTML5 的游戏机制。后续根据新增候选的源码窗口追踪 `mt_LastGame_ID` 的初始赋值与分支触发，再补充原版运行轨迹及双端对照。

### 2026-11-02 02:13 UTC 实际 FFDec 证据（非合成测试）

从成功的 [SWF 审计运行](https://github.com/mjw3177109/motafukepygame/actions/runs/41376489569) 的 `original_say08_handoff.json` 中，实际检出 **3 处** `mt_LastGame_ID` 写入文本候选：

| 来源（`scripts/` 下） | 行 | 文本写入及邻近条件 |
| --- | ---: | --- |
| `frame_4346/DoAction.as` | 411 | `mt_LastGame_ID = 0;`，位于初始属性赋值块 |
| `frame_4346/DoAction_2.as` | 742 | `_root.mt_LastGame_ID = 1;`，邻近条件 `Number(eval(temp_lines)[temp_x][temp_y]) == 24 && _root.mt_changes == 1 && _root.my_love == 0` |
| `frame_4346/DoAction_2.as` | 1295 | `_root.mt_LastGame_ID = Number(_root.save_mt_LastGame_ID);`，位于存档属性恢复块 |

对应 FFDec 源文件 SHA256：

- `frame_4346/DoAction.as`：`2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c`
- `frame_4346/DoAction_2.as`：`0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034`

**后续优先级**：独立验证第 742 行的事件入口与第 1295 行的存档恢复入口，并取得原版实机状态轨迹；不能把三个文本写入候选误认为全部运行时赋值路径或已证明结局。
