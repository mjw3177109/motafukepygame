# Kaggle 强化学习（未解锁）

严格顺序：SWF 取证 → Pygame + HTML5 原版一致性 → 全楼层和结局对照 → RL 环境映射 → Kaggle 训练 → 真正游戏内自主通关回放。

当前 **禁止启动实际训练**：原版规则尚未提取验证。`python rl/train_gate.py` 将拒绝缺失验收证据的任务。

未来实现：共享游戏核心逻辑的 Gymnasium 包装，优先 PPO/DQN 对照，并加入长程规划、资源预算与可复现随机种子；Kaggle Notebook 使用 Dataset 载入验证好的环境与模型，输出训练曲线、checkpoint 和实际通关回放，回传 GitHub 工作流产物。训练过程中不在代码仓库中提交 Kaggle API Token。
