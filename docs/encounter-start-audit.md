# 魔塔 1.12：Move_arrow 怪物准入 → 战斗帧 1 的状态交接

证据：`game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`，FFDec 导出 `export/scripts/frame_4346/DoAction_2.as` 的 `function Move_arrow` 怪物分支，和 `export/scripts/DefineSprite_453_mt_other_04/frame_1/DoAction.as`。

原版的执行顺序是：按目标格 40–70、188、198 查怪物 ID；ID=19 且 `Now_line<22` 时**即使不能开战**也先写 `boss_kills=1`；计算可开战条件；拒绝时播放 `music_10`；允许时设置 `Now_boss_id`、`Now_key_flag=0`、`Display_kill=1`；对 60/52/50/57 四种格子先分别扣除固定 100、固定 300、`int(HP/4)`、`int(HP/3)`，播放对应音效；再用扣除后的 HP 初始化战斗 sprite 右侧 HP，并记录 `Now_boss_x/y`。角色当前位置和怪物地图格均**不在这个阶段清除或改变**。

`core/encounter_start_probe.py` 与 `web/encounter_start_probe.mjs` 仅组合已经独立验证的 `preview_encounter` 和 `begin_battle`，并执行上述可见状态交接。输入为原版 11×11 格子状态、Flash 方向 ID、`original_tables.json` 的 `monsters` 对象；返回副作用描述和战斗初始快照，不执行真实声音、动画、键盘门禁、回合循环、奖励或结局。

双端共享 `tests/fixtures/encounter_start_cases.json`：普通开战、攻击不足、HP 不足、四种特殊伤害、19 号怪物跨楼层边界、188 号特殊 BOSS；额外验证输入不变、地图不被提前清除、战斗 HP 已扣除特殊伤害及未支持目标严格拒绝。

**范围限制：** 此处只证明原始 ActionScript 中这段状态交接的静态复现与跨语言测试一致，不是原版播放器逐帧对照；完整游戏输入门禁、sprite 实际执行时间和 Pygame/HTML5 界面仍待实现。不得据此解除 Kaggle 训练门禁。
