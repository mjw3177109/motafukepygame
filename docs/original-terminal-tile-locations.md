# 原版结局/第八组对话事件：初始地图位置取证

本次把已核验的原版 ActionScript 条件与同一 game.swf 提取并逐格核验的 27 层初始地图交叉检查。新增工具 tools/audit_terminal_tile_locations.py 同时复用 3267 格来源比对和结局条件来源审计，要求 SWF 哈希一致。

| 事件 | 初始地图出现位置（原始数组下标） | 触发条件 |
| --- | --- | --- |
| 地图格 129：启动 mt_say_08 | mt_line_19[7][5]，仅一处 | Display_say[8] == 0 |
| 地图格 24：设置 mt_LastGame_ID = 1 | mt_line_00[8][5]、mt_line_22[2][6]，共两处 | mt_changes == 1 && my_love == 0 |

上述位置是初始静态数组的 [outer_index][inner_index]，不是已确认的屏幕 (x,y) 坐标；不能推断玩家一定能到达、进入事件判断，或剧情修改后仍保留该格。temp_lines 的运行时选择、动态地图变化、事件顺序、存档恢复、Flash 实机结局和 Pygame/HTML5 双端回放均未验证。

CI 在验证原版楼层表后运行新审计，并归档 original_terminal_tile_locations.json。校验楼层形状、事件格位置/数量、原版事件条件及来源哈希；出现变化即失败关闭。下一步核对 temp_lines 的来源与动态事件写入，再采集原版 Flash 操作轨迹。Gymnasium/Kaggle 门禁继续关闭。


## Move_arrow 楼层选择与地图坐标的源码绑定（新增）

本轮从已归档且通过来源哈希校验的 `scripts/frame_4346/DoAction_2.as` 中，核对 `Move_arrow(arrow_id)` 函数。原版在 `Now_line < 10` 时使用 `"_root.mt_line_0" add Now_line`，否则使用 `"_root.mt_line_" add Now_line`。移动前以 `Now_xid`、`Now_yid` 初始化 `temp_x`、`temp_y`，事件查询为 `eval(temp_lines)[temp_x][temp_y]`。角色显示坐标的原始赋值为 `_x = 207 + temp_y * 32`、`_y = 47 + temp_x * 32`。这说明数组外层对应显示纵向、内层对应显示横向；仍不代表已经验证 Flash 运行时渲染或点击位置。

同一 `Move_arrow` 函数内，编号 129 的事件条件出现 1 处，编号 24 的事件条件出现 4 处（含不同剧情条件）；不能把编号 24 的所有触发都解释为结局状态写入。新增 `tools/audit_move_arrow_binding.py` 和 8 项失败关闭测试，检查楼层补零、索引初始化、屏幕坐标映射、事件查询所在函数及条件出现次数。审计重读源文件并复核 SHA256，结果写入原有 `original_terminal_tile_locations.json` 的 `move_arrow_lookup` 字段。

**验收边界：** 本轮只确认静态源码关系，不证明实际楼层切换、动态地图修改、事件可达性、存档往返、原版结局或 Pygame/HTML5 行为一致。下一步按真实 Flash 轨迹验证 `Move_arrow` 的事件状态转换，Gymnasium/Kaggle 门禁保持关闭。


## 地图格 24 的四条独立分支：静态顺序与作用域审计

基于同一份通过 SHA256 清单核验的原版 scripts/frame_4346/DoAction_2.as，Move_arrow(arrow_id) 中地图格 24 的四个条件是按源码顺序排列的四个独立 if，不是 if/else if 互斥链：

1. 第 710 行：Display_say[0] == 0，启动第一组对话。
2. 第 734 行：mt_changes == 1 && my_love == 0，执行 say_three，清除 mt_changes 并写入 mt_LastGame_ID = 1。
3. 第 744 行：my_love == 1，选择相关对话、修改 mt_line_20[7][5]，并清除 my_love、mt_changes。
4. 第 762 行：Now_line == 22，根据三项 mt_GetMoney 状态选择 say_six 或 say_five。

新增 tools/audit_tile24_branch_order.py 和 8 项回归测试，核对四个守卫的存在、数量、顺序及关键写入是否仍处于对应的花括号作用域。结果作为 original_terminal_tile_locations.json 的 tile24_branch_order 字段归档，保留运行时验证为 false。尤其注意：多个独立 if 可能在一次调用中依次满足；目前未证明实际是否会连续执行，也不能把上述静态分支视为剧情或结局已通过验收。下一步应在原版 Flash 中采集 tile-24 触发前后状态轨迹，并在 Pygame/HTML5 双端重放。强化学习门禁不变。


## 地图格 24：`my_love == 1` 的双分支防漏审计

复核原版 FFDec 导出的 `Move_arrow` 源码发现：第三条独立 `if` 内还有一层 `mt_GetMoney[0] == 1` 的 `if/else`。持有该状态时进入 `say_four`，否则进入 `say_two`；**两个分支均写入** `mt_line_20[7][5] = 13`。此前审计只要求在外层块内找到一次地图写入，可能漏掉另一分支的错误。

本轮在 `tools/audit_tile24_branch_order.py` 中分别校验两条子分支的对话标签及地图写入，并新增四项失败关闭回归。证据归档新增 `love_dialogue_both_arms_verified`（仅表示静态源码结构）。原版 Flash 运行轨迹、实际道具状态、双端执行结果与结局仍未验收；Gymnasium/Kaggle 门禁继续关闭。


## 地图格 24：第 22 层三项道具条件与双对话分支（本轮）

从 2026-11-02 的 GitHub Actions 原版 FFDec 归档（SWF SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`，`scripts/frame_4346/DoAction_2.as` SHA256 `0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034`）核对 `Move_arrow` 第 762–775 行。地图格 24 的第四条独立守卫为 `Now_line == 22`。进入后先清除 `Now_key_flag`、设置 `Display_say[0] = 1` 并创建 `mt_say_01` 剪辑，再根据 `Number(mt_GetMoney[0]) == 1 && Number(mt_GetMoney[1]) == 1 && Number(mt_GetMoney[2]) == 1` 选择 `say_six`；其余情况进入 `say_five`。

新增静态失败关闭审计要求三个道具下标和 AND 条件精确匹配、前置对话设置在分支选择之前、`if/else` 两臂分别包含正确对话标签；新增 6 项回归测试。输出 `floor22_three_item_both_arms_verified` 只代表原版静态源码审计，不代表游戏事件可达、真实执行顺序、双端复刻或结局通过。下一步应建立原版 Flash 操作轨迹并与 Pygame/HTML5 两端对照；Gymnasium/Kaggle 门禁保持关闭。
