# 战斗结束与奖励链：原版 ActionScript 静态取证

原始 game.swf SHA256：04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9。
取证来源：GitHub Actions run 41340994936、artifact 13096754909 中的 FFDec 原始导出归档。

- frame54（已有独立审计）：将 right_hp 写回 Now_hp，设置 Display_kill=2。
- export/scripts/DefineSprite_855/frame_1/DoAction.as，SHA256 fdc32d3bc0ab4e511aade04b38a8b336030c33096c7ce3f4d14b58f5f9b1f0a6：Display_kill==2 时清除战斗剪辑，复位标志并调用 Move_arrow(100)。
- export/scripts/frame_4346/DoAction_2.as，SHA256 0de19a0338cd966446acb4fd2acb82f82cf77992c8839356e17afc8f3085d034：arrow_id==100 时清除怪物格、增加金币和经验、刷新 HP 显示。

**严格范围：**仅上述两个局部条件块未包含 Now_hp/right_hp 死亡条件。由此可建立合成 HP=0、HP=-15 的双端奖励探针回归，但绝不证明 Flash 实机中其他脚本不会提前终止，也不证明真实死亡、结局或通关。game_over 标签也用于剧情结局，不能擅自当作死亡事件。

执行：python -m tools.audit_original_battle_completion --export-root .swf_audit/export --swf game.swf --out .swf_audit/original_battle_completion_audit.json

GitHub Actions 重新读取 SWF 与两份完整 FFDec 脚本并校验字节哈希、局部条件块与顺序；JSON 证据标记静态源码通过，Flash 播放、死亡与 RL 均未验证。

下一步：检查其余脚本中的 HP/死亡分支、game_over 触发条件，获取真实 Flash 实机轨迹；原版地图、结局与双端全流程人工验收完成前不启动 Gymnasium/Kaggle。
