# 魔塔 1.12 — Flash 原版复刻工程

> **状态：SWF 取证与基础设施阶段。尚未完成 1:1 复刻，不得标注“可玩完整版”。**

## 原版文件与两端目标

本仓库实际原版文件为 `game.swf`（不是 `ame.swf`）；自带 `FFDec/` 和 `FFDec/ffdec.jar`。

目标运行端为 **Pygame（Python）** 和 **HTML5 Canvas（浏览器）**，共用从原始 ActionScript 提取并校验的地图、角色、怪物、数值、商店、事件、道具、剧情、存档与结局数据；不能以自行编造的地图或近似数值冒充原版。

工作顺序：

1. 先从 `game.swf` 导出 Tag、ActionScript、图片、声音、字形等素材并存储带哈希的取证清单。
2. 从 ActionScript 确认游戏的实际公式、楼层地图、敌人表、事件触发、特殊规则、胜负与结局。
3. 建立**同一份规格**下的 Pygame/HTML5 双端实现；对照原版逐步记录操作轨迹与截图。
4. 各层回放、战斗 HP/攻击/防御/钥匙等逐步严格一致；关键截图人工审阅通过才可将状态标注 1:1。
5. 完成游戏一致性验收之后，才建立基于真实规则的 Gymnasium 强化学习环境、Kaggle Notebook 训练与通关验证。

## 本阶段使用

```bash
# Python 3.11+，SWF 元信息分析（不依赖 FFDec）
python tools/swf_probe.py game.swf

# 完整 FFDec 导出：Java 8（仓库自带 FFDec）
python tools/extract_swf.py --swf game.swf --ffdec FFDec/ffdec.jar --out .swf_audit

# 工具单测
python -m unittest discover -s tests -v

# 原版轨迹与重构版轨迹 1:1 比较（必须提供真实轨迹）
python tools/verify_parity.py --golden evidence/original.jsonl --candidate evidence/pygame.jsonl
```

GitHub Actions 中 `SWF Original Audit` 会使用 Java 8 导出结果并上传工作流 artifact，不会提交庞大的反编译产物到 git。

## 不变的验收原则

- **禁止假数据**：没有原版提取依据不生成所谓“原版地图/怪物表/音效”。
- **禁止阶段跳跃**：未通过全流程一致性验收前不执行 Kaggle 正式训练。
- **不能把 FFDec 的导出成功等同于 1:1 复刻完成**：手工逻辑复原、原版对照与画面验收仍是必要工作。
- **每次变更必须可追溯**：新增文件、修改目录、测试证据和剩余缺口在 PR/审计中更新。
- 相关 SWF 与音视频的分发应确认拥有合法使用与再发布权。
