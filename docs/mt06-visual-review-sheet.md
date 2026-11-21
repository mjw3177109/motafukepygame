# mt_06 双端视觉审核图（非 Flash 原版基准）

本工具读取已归档的 `mt_06_pygame.png`、`mt_06_chromium.png`、渲染报告与独立 SWF/Shape 锚点，先调用 `verify_mt06_artifacts.verify` 复核原始 PNG 字节与差异统计，再生成 `visual_review.png` 和 `visual_review.json`。

- 左：Pygame/CairoSVG；中：Chromium/Canvas；右：RGBA 差异掩码。红色表示 RGB 差异，品红表示 Alpha 差异，黑色表示相同。放大使用最近邻采样，不改变原始 64×64 的统计。
- **不含原版 Flash 播放器截图**；本图只能用于两端渲染差异的人工定位，不证明任何一个渲染结果符合 Flash。
- 报告固定 `original_flash_reference_available=false`、`flash_visual_parity_verified=false`、`runtime_binding_approved=false`、`gymnasium_ready=false`、`kaggle_started=false`。
- 若输入 PNG、来源锚点或统计不一致，工具在生成审核图之前拒绝执行。

后续应从可核查的 Flash 运行环境捕获相同帧、相同视口、相同缩放的原版图像，记录播放器版本、原始 SWF SHA256、截图哈希、场景/帧号与捕获方法。独立人工审核通过前不得建立正式绑定。
