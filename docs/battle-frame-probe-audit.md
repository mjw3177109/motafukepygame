# 原版战斗动画逐步执行探针（有限范围，非完整战斗）

原版 game.swf SHA256: 04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9。
FFDec 导出路径：export/scripts/DefineSprite_453_mt_other_04/frame_{1,24,34,35,54}/DoAction.as。

- frame 1：kill_left=max(0,left_gong-right_fang) 是怪物对英雄的伤害；kill_right=max(0,right_gong-left_fang) 是英雄对怪物的伤害；kill_number=0，英雄先攻击。
- frame 24：if(left_hp>0 || right_hp>0) 才执行动作。偶数回合先 random(200)；若随机数 <= _root.Now_life，英雄伤害翻倍。怪物 HP 向零以下截断到零。奇数回合怪物对英雄反击，英雄 HP 不截断；若此时怪物 HP 为零，才 gotoAndPlay(35)。
- frame 34：怪物 HP 大于零才循环 gotoAndPlay(24)。
- frame 35/54：胜利动画/状态交接；frame 54 才把 right_hp 赋给 _root.Now_hp 并设置 Display_kill=2。本探针只返回 jump_to_35，不提前执行奖励、死亡或状态交接。
- random(200) 的 0..199 结果由外部调用者显式提供，方便测试固定随机序列；并非猜测随机种子或以平均伤害代替。
- 原版战斗准入和特殊即时扣血由 Move_arrow 负责，必须先执行，然后才可按 frame 1/24 运行。本探针没有自动完成这个连接，也不模拟真实帧间隔、Flash UI、音效和动画。

此版本提供 Python / JavaScript 两端共享的确定性 fixture，包含直接调用奇数回合分支时怪物已零血的输入、反击使英雄 HP 为负、暴击边界、双方零血停顿等。注意：奇数回合且怪物已零血的独立输入不代表原版 frame34 会在英雄一击击杀后再安排反击；真实循环条件见 `docs/battle-timeline-audit.md`。它验证脚本静态分支而非 Flash 真机回放；未验收的游戏行为与 RL 训练门禁不变。
