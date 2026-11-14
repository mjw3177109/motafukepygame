# 原版死亡与结局脚本候选索引（只读取证）

本阶段不猜测 `game_over` 的语义，也不把负 HP、奖励发放或结局帧视为死亡证据。新增 `tools/audit_terminal_candidates.py`：在 GitHub Actions 使用原始 `game.swf` 的固定 SHA256 和 FFDec `manifest.json`，逐个校验所有导出 `.as` 文件的字节 SHA256、长度与完整清单，然后列出 `game_over` 文本及 `Now_hp/right_hp` 比较表达式的源码文件、行号和片段。

**验收边界**：这是全脚本的文本候选检索，不是 ActionScript 控制流证明；可能匹配注释、无关剧情、反编译片段，也可能遗漏跨行特殊表达式。若 `game_over` 是 SWF 帧标签而非脚本字符串，零命中也不等于不存在。审计结果永远标记 Flash 实机、死亡、结局、双端 1:1 和 Gymnasium/Kaggle 为未验证。

执行：

```bash
python -m tools.audit_terminal_candidates --manifest .swf_audit/manifest.json --export-root .swf_audit/export --swf game.swf --out .swf_audit/original_terminal_candidates.json
```

输出 JSON 随 SWF 审计归档，日志展示前 24 个候选。下一轮根据真实候选路径逐项追踪调用者、帧标签、状态转移，再为 Pygame 与 HTML5 建立有来源的死亡/结局回归。不得据此开放强化学习门禁。

## 新增：两处 game_over 的可复核源码上下文

索引现在对每个命中保留前 24 行、后 8 行的原始 FFDec 反编译文本窗口，记录行号、400 字符截断标记，并保留完整 ActionScript 文件 SHA256。CI 日志额外输出两处 `game_over` 的窗口，审计 JSON 保存所有候选窗口，便于核对 Sprite 855 第 9 行与第 206 行的相邻条件及分支。此处只提供可审阅的邻近源码，**不自动推断所在 if 分支、死亡语义、结局语义或 Flash 实机执行路径**。文本窗口跨越代码块时也不代表执行关系，后续必须结合 ActionScript 控制流和实机轨迹验证。

## 2026-11-01 源码窗口实测（不是运行时结论）

在 [SWF 审计 PR run 41355793449](https://github.com/mjw3177109/motafukepygame/actions/runs/41355793449) 的 FFDec 164 个脚本来源哈希校验通过后，`scripts/DefineSprite_855/frame_1/DoAction.as` 的相邻源码显示：

- 第 9 行 `gotoAndPlay("game_over")` 位于 `Display_text == 2` 条件内，并嵌套 `Number(mt_line_26[3][5]) == 0`；在跳转前调用 `DelBaseDisplay()` 和 `DelLineDisplay()`。
- 第 206 行同名跳转位于 `Display_say[8] == 9` 条件内，并嵌套 `mt_LastGame_ID == 0`；前面将 `Display_say[8]` 改为 10、`Now_key_flag` 改为 1，跳转前同样清理显示。紧接着的 `mt_LastGame_ID == 1` 分支还修改第 21 层地图并复制/删除剪辑。
- 本次两处源码窗口**均未显示直接的玩家 HP 死亡条件**。这是局部文本证据，不排除更早的状态变更或其他脚本跳转；不能据此把 `game_over` 判定为死亡界面，也不能证明实际结局路径。

下一步：从原始 ActionScript 追溯 `Display_text`、`mt_line_26[3][5]`、`Display_say[8]`、`mt_LastGame_ID` 的赋值点和触发事件，并通过 Flash 实机轨迹确认两个分支的实际意义。不得在此之前更改双端死亡/结局机制或开放 RL 门禁。


## 2026-11-01 增量：结局相关状态写入候选索引

同一条已校验 SWF SHA256 + FFDec 完整脚本清单的 CI 链，现在还索引 \`Display_text\`、\`mt_LastGame_ID\`、\`Display_say\`（含下标）和 \`mt_line_26\`（含下标）的文本赋值、复合赋值及后置自增/自减。结果在 \`.swf_audit/original_terminal_candidates.json\` 的 \`terminal_state_write\` 候选中保留文件、行号、完整脚本 SHA256、目标、运算符和相邻源码；\`state_write_candidate_count\` 单独计数，不改变旧候选计数字段。此索引用于定位潜在状态来源，不是 ActionScript 解析器，可能包含注释或无法执行的分支，亦可能漏掉间接赋值。只有源码控制流与 Flash 实机回放确认后，才能将候选写入转成双端游戏规则。新增 4 项测试覆盖写入、比较误判、动态下标和哈希篡改拒绝。

## 2026-11-02 增量：同一行多次状态写入不得漏记

修复候选索引在同一行仅保留一个 `terminal_state_write` 的问题。FFDec 的 ActionScript 可能将多个赋值、复合赋值或自增表达式放在一行；旧的 `(kind, line)` 去重键会悄悄漏掉后续写入。现在对状态写入按源码偏移分别保留，并增加 1 起始的 `column` 字段；旧的 `game_over_mention`、`hero_hp_comparison` 仍保持逐行候选计数。增加同一行四种状态写入、重复目标两次赋值及非写入候选去重的回归测试。

这只改善原始反编译文本的取证完整性，**不**证明这些写入会执行，也不证明它们构成游戏结局控制链。审计仍需 SWF 哈希、导出清单和逐文件 SHA256 校验；Flash 实机轨迹、死亡/结局、双端一致性与 Kaggle 门禁状态均保持未验收。
