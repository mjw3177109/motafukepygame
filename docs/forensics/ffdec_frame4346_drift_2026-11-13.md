# FFDec frame_4346/DoAction.as 双次导出差异：2026-11-13 取证

来源：GitHub Actions [SWF Audit #43407761711](https://github.com/mjw3177109/motafukepygame/actions/runs/43407761711)，artifact [14028057326](https://github.com/mjw3177109/motafukepygame/actions/runs/43407761711/artifacts/14028057326)。本记录基于下载 ZIP 后对两份原文执行逐行 diff、字节长度和 SHA-256 计算；不代表 Flash 运行行为已经验收。

- SWF SHA-256：`04b317b7fd9d32c5b083c993e99a3eea527f392e5fc938d23928e953bb638db9`
- 两次导出各 911 个文件；路径集合相同，仅 `scripts/frame_4346/DoAction.as` 的内容不同。
- 第一次：421 行，20,710 字节，SHA-256 `2372dc16f71b6ede1110b61101b47ff11dd529803fc4077accd075381bffe97c`。
- 第二次：247 行，13,029 字节，SHA-256 `4e92fa52a29df1c6acfcdd4475bdecf97fb0b97ac5fd6f9d1cc0e3b6e2e700f4`。
- 两份文件前 247 行附近开始分叉：第二份在 `mt_line_20[4] = new Array(62,7,58,0,0,97,0,0,58,7,62);` 后停止后续地图/初始化赋值，结尾另有独立表达式 `"mt_line_20";`；第一份继续包含 `mt_line_20[5]` 至 `mt_line_26`、`boss_man` 等初始化，末尾是 `NowGameTime = _root.StartGameTime;`。
- **结论限度**：两份反编译文本明显不完整或不等价；不能据此确定哪份完整、也不能直接断言原始 SWF 的执行逻辑不稳定。此处是 FFDec 导出可靠性缺口，不能把任意一次导出当作无条件可信的地图/怪物数据来源。
- 既有 fail-closed 双导出比较已正确拦截本次差异。下一步应对照原始 SWF 的 ActionRecord 字节范围/动作数、尝试 FFDec 版本与命令参数复现，并对地图和怪物数据使用独立 SWF 标签证据核对；不得为让 CI 变绿而忽略该差异。
- 仍有 8 组大小写路径冲突。动态战斗、地图事件、结局、Flash 视觉基线和双端 1:1 均未因此通过验收；Gymnasium/Kaggle 门禁保持关闭。
