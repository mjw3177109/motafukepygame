# 魔塔 1.12：frame24 → frame34 → frame35 的真实战斗循环

原版 SWF：`game.swf`，SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`。

取证来源（FFDec 导出）：`export/scripts/DefineSprite_453_mt_other_04/frame_24/DoAction.as`、`frame_34/DoAction.as`、`frame_35/DoAction.as`、`frame_54/DoAction.as`。

**关键发现：** 原版 frame24 进行一次攻击或反击，随后到 frame34；frame34 仅在 `left_hp > 0` 时 `gotoAndPlay(24)`。若英雄在 frame24 的偶数次攻击直接把怪物打至零血，则 frame34 不再循环，进入 frame35；**此时不会无条件多执行一次怪物反击**。原先单独测试 `step_battle_frame` 在“怪物已经死亡且 kill_number 为奇数”时的反击分支，不能据此推断完整 Flash 时间轴会走到该状态。frame35 播放 `music_07`；frame54 才将 `right_hp` 写回英雄并置 `Display_kill=2`。

新增 `core/battle_timeline_probe.py` / `web/battle_timeline_probe.mjs`，在已有 frame24 纯函数之上显式模拟 frame34 的循环决定。共享 `battle_timeline_cases.json` 测试：一击必杀不反击、三次攻击仅两次反击、暴击击杀、无伤反击、随机序列不足或过多、有限步上限。另通过独立的 encounter、timeline、frame54、settlement 探针验证一条普通怪物链路的状态与金币经验变化。

**验收边界：** 这只复现脚本的确定性控制分支，不模拟 frame25–33 的时间、帧间动画、音乐播放、死亡/结局、其他同格事件或原版 Flash 播放器录像。测试中的怪物数值是特定规则向量，不代表完整地图通关。没有真实逐操作与逐帧证据，不得标注 Pygame/HTML5 已达到 1:1，也不得解锁 Kaggle 强化学习。
