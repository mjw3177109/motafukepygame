# 原版结局/第八组对话事件：初始地图位置取证

本次把已核验的原版 ActionScript 条件与同一 game.swf 提取并逐格核验的 27 层初始地图交叉检查。新增工具 tools/audit_terminal_tile_locations.py 同时复用 3267 格来源比对和结局条件来源审计，要求 SWF 哈希一致。

| 事件 | 初始地图出现位置（原始数组下标） | 触发条件 |
| --- | --- | --- |
| 地图格 129：启动 mt_say_08 | mt_line_19[7][5]，仅一处 | Display_say[8] == 0 |
| 地图格 24：设置 mt_LastGame_ID = 1 | mt_line_00[8][5]、mt_line_22[2][6]，共两处 | mt_changes == 1 && my_love == 0 |

上述位置是初始静态数组的 [outer_index][inner_index]，不是已确认的屏幕 (x,y) 坐标；不能推断玩家一定能到达、进入事件判断，或剧情修改后仍保留该格。temp_lines 的运行时选择、动态地图变化、事件顺序、存档恢复、Flash 实机结局和 Pygame/HTML5 双端回放均未验证。

CI 在验证原版楼层表后运行新审计，并归档 original_terminal_tile_locations.json。校验楼层形状、事件格位置/数量、原版事件条件及来源哈希；出现变化即失败关闭。下一步核对 temp_lines 的来源与动态事件写入，再采集原版 Flash 操作轨迹。Gymnasium/Kaggle 门禁继续关闭。
