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
