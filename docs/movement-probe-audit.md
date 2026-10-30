# 原版 Move_arrow 第一批确定性规则（取证限定）

证据：`game.swf` SHA256 `04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`，FFDec 导出的 `export/scripts/frame_4346/DoAction_2.as` （SHA256 `0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034`）中 `function Move_arrow(arrow_id)`；键盘按键关联见 `export/scripts/DefineButton2_856/BUTTONCONDACTION on(keyPress Up).as` 与 `...Down).as`。

原始坐标 `mt_line_XX[Now_xid][Now_yid]`：第一个索引是**行**（画面 Y），第二个索引是**列**（画面 X）。Flash `arrow_id=1` 左、`2` 右、`3` 上、`4` 下。空地 `0` 移动一步；墙 `1` 不移动。钥匙 `6/7/8` 分别增加黄/蓝/红钥匙，门 `2/3/4` 分别消耗对应钥匙。红宝石 `10` 攻击 +3，蓝宝石 `9` 防御 +3，药瓶 `11/12` 生命 +200/+500。**钥匙/门/道具交互发生时，原版 Move_arrow 本次调用不会立即更新人物位置；它只清除目标格并触发 UI/动画，后续再次移动才可进入该格。**

`core/movement_probe.py` 与 `web/movement_probe.mjs` 是相同规则的最小、纯函数验证探针，使用 `tests/fixtures/movement_probe_cases.json` 进行跨端测试。它们不是已完成的 Pygame/HTML5 游戏，也不负责播放原版素材或接管键盘输入。仅能在原版 `Now_key_flag`、对话框、商店、战斗等输入门禁已允许移动时调用。输入快照为 `{grid:11x11,row,col,hp,attack,defense,keys:{yellow,blue,red}}`；返回 `{state,event}`。

未验证的楼梯 `13/14`、怪物 `40..70`、特殊通行格 `97..99`、商店/对话/道具事件均**抛出异常**，不得将其当作空地或墙来冒充原版。此模块没有全局动画、声音、楼层切换、死亡/通关、原版录像回放证据。未来逐项补足这些状态，并以原版轨迹和截图验证后才能集成到 Pygame/HTML5 正式客户端。
