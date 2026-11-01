# 原版死亡与结局脚本候选索引（只读取证）

本阶段不猜测 `game_over` 的语义，也不把负 HP、奖励发放或结局帧视为死亡证据。新增 `tools/audit_terminal_candidates.py`：在 GitHub Actions 使用原始 `game.swf` 的固定 SHA256 和 FFDec `manifest.json`，逐个校验所有导出 `.as` 文件的字节 SHA256、长度与完整清单，然后列出 `game_over` 文本及 `Now_hp/right_hp` 比较表达式的源码文件、行号和片段。

**验收边界**：这是全脚本的文本候选检索，不是 ActionScript 控制流证明；可能匹配注释、无关剧情、反编译片段，也可能遗漏跨行特殊表达式。若 `game_over` 是 SWF 帧标签而非脚本字符串，零命中也不等于不存在。审计结果永远标记 Flash 实机、死亡、结局、双端 1:1 和 Gymnasium/Kaggle 为未验证。

执行：

```bash
python -m tools.audit_terminal_candidates --manifest .swf_audit/manifest.json --export-root .swf_audit/export --swf game.swf --out .swf_audit/original_terminal_candidates.json
```

输出 JSON 随 SWF 审计归档，日志展示前 24 个候选。下一轮根据真实候选路径逐项追踪调用者、帧标签、状态转移，再为 Pygame 与 HTML5 建立有来源的死亡/结局回归。不得据此开放强化学习门禁。

## 新增：两处 game_over 的可复核源码上下文

索引现在对每个命中保留前 24 行、后 8 行的原始 FFDec 反编译文本窗口，记录行号、400 字符截断标记，并保留完整 ActionScript 文件 SHA256。CI 日志额外输出两处 `game_over` 的窗口，审计 JSON 保存所有候选窗口，便于核对 Sprite 855 第 9 行与第 206 行的相邻条件及分支。此处只提供可审阅的邻近源码，**不自动推断所在 if 分支、死亡语义、结局语义或 Flash 实机执行路径**。文本窗口跨越代码块时也不代表执行关系，后续必须结合 ActionScript 控制流和实机轨迹验证。
