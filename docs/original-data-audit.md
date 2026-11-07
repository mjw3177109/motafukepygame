# Flash 1.12 原版静态数据取证（2026-10-30）

## 可复核来源

- 原版文件 game.swf，SHA256：04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9。
- FFDec 导出：GitHub Actions SWF Original Audit，脚本 export/scripts/frame_4346/DoAction.as。
- 该 ActionScript 文件 SHA256：2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c。
- 自动解析工具：tools/extract_original_tables.py；输出 original_tables.json 随工作流 Artifact 保存，不修改原始 SWF。
- 数据包含 27 组 mt_line_00 至 mt_line_26，每组 11×11；33 个 boss_man[0..32]；9 项 Base_* 初始值。
- 已核对 Base_hp=1000、Base_gong=10、Base_fang=10、Base_life=1。

## 1:1 约束

解析结果保留 mt_line_XX[outer_index][inner_index] 原始索引顺序；尚未依据原版渲染逻辑证明横纵坐标含义，不能擅自转置。怪物数组的五个数字和名称保持原始顺序，具体字段语义须与战斗、金币及经验代码交叉核实。此 JSON 是**初始静态表**，并不代表全部剧情触发、地图动态变化或战斗公式。

后续须审查 frame_4346/DoAction_2.as 的 Move_arrow、SetLineDisplay 和相关 Sprite/按钮脚本，提取道具 ID、碰撞、战斗特殊规则、楼层跳转及结局条件，再通过原版操作轨迹验收 Pygame 与 HTML5。注意：战斗逻辑存在条件分支，不能仅凭怪物数值表自行实现通用公式。

## 重现

运行 GitHub Actions 的 SWF Original Audit 工作流，下载 original-flash-audit Artifact，查看 original_tables.json 与 manifest.json。本步骤仅确认提取完整性，**不代表游戏 1:1 复刻已完成**，更不允许提前解锁 Kaggle 强化学习训练。
