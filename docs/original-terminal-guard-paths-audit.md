# 魔塔 Flash 1.12：结局状态事件与存档路径审计

本轮只增加原版 ActionScript 的**失败关闭静态来源审计**，不修改 Pygame/HTML5 游戏规则。复用原始 game.swf SHA256、FFDec 脚本清单和逐文件字节哈希校验。

依据 2026-11-02 02:15 UTC [原版审计归档](https://github.com/mjw3177109/motafukepygame/actions/runs/41376633416) 内的 ffdec_export.tar.gz，核对以下源码锚点：

| 原版 FFDec 来源 | 文本证据 |
| --- | --- |
| frame_4346/DoAction.as:411 | 初始化 mt_LastGame_ID = 0 |
| frame_4346/DoAction_2.as:734-743 | 同一条件块：地图格值 24，mt_changes == 1，my_love == 0；随后 mt_GetMoney[0] = 1，mt_changes = 0，mt_LastGame_ID = 1 |
| frame_4346/DoAction_2.as:1194 | SaveData() 保存 mt_LastGame_ID |
| frame_4346/DoAction_2.as:1295 | LoadData() 恢复 mt_LastGame_ID |
| frame_4346/DoAction_2.as:1153-1155,1253-1255 | 保存/读取 Display_say 数组的循环；上限是 save_Display_say.length |

工具：tools/audit_terminal_guard_paths.py。运行：

    python -m tools.audit_terminal_guard_paths --manifest .swf_audit/manifest.json --export-root .swf_audit/export --swf game.swf --out .swf_audit/original_terminal_guard_paths.json

审计不只全文搜索赋值，还检查赋值处于指定事件条件块及 SaveData/LoadData 函数作用域。允许 LF/CRLF；改变条件、把赋值移出条件块、颠倒保存与恢复、删除对话状态循环、修改来源字节或 SWF 哈希时必须失败。JSON 记录来源 SHA256、行号及未验证标志。

**限制**：这是针对当前 FFDec 结构的文本锚点，不是通用 ActionScript AST；顶层函数闭括号依赖 FFDec 当前格式，漂移时应失败关闭。未执行真实存档往返，未验证 save_Display_say 数组长度、事件可达性、玩家选择、game_over 语义、Flash 原版结局或双端 1:1。此前第八组对话与 Sprite 855 的静态交接证据仍需原版运行轨迹支持。

下一步优先采集 Flash 实机地图格 24 触发、保存/读取前后 mt_LastGame_ID 和 Display_say[8] 的真实状态，再构造 Pygame/HTML5 事件序列回归。Gymnasium/Kaggle 门禁继续关闭。
