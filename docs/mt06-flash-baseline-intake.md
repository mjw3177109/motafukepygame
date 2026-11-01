# mt_06 独立 Flash 截图接入（非视觉验收）

**当前没有真实 Flash 播放器截图。** 本轮增加工具 tools/audit_mt06_flash_baseline.py，缺少截图时报告 flash_capture_status=missing，绝不使用 Pygame/Chromium 图片冒充原版。

真实截图接入位置：data/flash_baselines/mt_06/。该目录应包含：

- original_stage.png：独立 Flash 兼容播放器直接截取的完整舞台，RGB/RGBA PNG。
- reference_crop.png：从 original_stage.png **不缩放、不修饰**裁出的 64×64 PNG。
- capture.json：记录来源 SWF/Shape SHA256、播放器名称与版本、捕获方式、UTC 时间、场景与帧号、裁剪坐标、背景颜色及两张 PNG 的哈希。

示例 JSON（**占位值不是 Flash 取证**）：

\`\`\`json
{
  "schema_version": 1,
  "alias": "mt_06",
  "swf_sha256": "04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9",
  "source_svg_sha256": "15e5960bf4064c15af2b7086b91e437c55ccbead25425ae40149fbda20a93a70",
  "player_name": "ACTUAL_PLAYER_NAME",
  "player_version": "ACTUAL_PLAYER_VERSION",
  "capture_method": "ACTUAL_CAPTURE_METHOD",
  "capture_utc": "2026-11-01T07:00:00Z",
  "scene_id": "ACTUAL_SCENE",
  "frame_index": 0,
  "crop_rect": [0, 0, 64, 64],
  "background_rgb": [255, 255, 255],
  "original_stage_sha256": "ACTUAL_SHA256",
  "reference_crop_sha256": "ACTUAL_SHA256"
}
\`\`\`

真实捕获必须保证 mt_06 与两端候选的场景、帧、像素比例、背景和坐标一致。工具先运行既有 verify_mt06_artifacts 来源审计，再检查截图哈希与原始舞台精确裁剪关系；然后将 Pygame/Chromium PNG 分别合成到记录的背景色，与 Flash 裁剪图进行 RGB 像素差异统计。

CI 自动生成 mt06_candidate/flash_baseline_audit.json。缺少目录时输出 missing 且不阻断其他取证；目录存在但证据损坏时 CI 失败。即使三方 RGB 完全相同，也不能自动证明播放器真实身份、原版机制一致或完成人工审核，所有视觉/正式绑定/玩法/Gymnasium/Kaggle 门禁继续关闭。

新增测试仅使用**合成测试图**，覆盖缺失、正确 RGB 比较、篡改、错误裁剪、错误来源、错误帧号、假审批与不完整目录。测试图绝不是原版 Flash 截图。
