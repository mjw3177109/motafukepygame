# 原版战斗结束状态交接（局部探针，不是完整战斗引擎）

原版 `game.swf` SHA256: `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`。

FFDec 证据与源码 SHA256：

- `export/scripts/DefineSprite_453_mt_other_04/frame_54/DoAction.as`：`112c9ad7454ad425124e1ccb6481ed71ddba58ad36ebc5dba6639a07f367893c`
- `export/scripts/DefineSprite_855/frame_1/DoAction.as`：`3c6de7a67bd0e02e57438ec13cbcd081f1a5487a981e1bb960f2e0872bdddb38`
- `export/scripts/frame_4346/DoAction_2.as`：`0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034`

已核对的原版顺序：战斗动画 frame54 令 `Display_kill=2`、`Now_hp=right_hp`；主循环 sprite855 在 `Display_kill==2` 时删除三个战斗动画实例，重置标志并调用 `Move_arrow(100)`；该回调显示奖励文本，按普通怪物单格或 BOSS 31/32 的 3×3 区域清除地图格子，累加金币 `boss_man[id][3]` 与经验 `boss_man[id][4]`（原版字段名 `Now_mp`），播放 `music_03`。BOSS 3×3 区域是 `[Now_boss_x-2..Now_boss_x] × [Now_boss_y-1..Now_boss_y+1]`，**不是以怪物位置为几何中心的 3×3**。

本轮 Python / JS 两个纯函数只模拟这段状态变化，显式要求动画已完成，拒绝重复发奖与非法坐标；保留原版 `right_hp` 可能为负的行为。测试覆盖普通怪物、两种 BOSS、负 HP、重复结算及越界。未模拟原版音画帧间隔、场景切换、额外同格事件、存档、胜负结局，也未运行 Flash 真机回放。测试通过不等于双端 1:1 游戏完成。
