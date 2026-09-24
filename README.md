# android-ai-test-skills

Android 设备黑盒 GUI 测试 v2：**AI 即执行者**。

对话里的 AI（CodeBuddy / Claude Code）直接驱动真机执行测试用例：每步调用薄工具层"看（observe）/ 动（act）/ 读（read）"，自行分析结果、规划下一步；可以从UIUX和知识卡片中查询已有知识；每步证据自动落盘，最终输出带证据的测试报告。

与 v1（AI 写 Python 用例脚本 → 确定性回放）的区别：**不再写 case**。
用例就是用户口述的步骤+预期，执行即探索，成功路径的知识沉淀进**知识卡**
（坑与行为规律）与**路径图**（在哪找什么）而不是代码。

**UIUX 知识库**保存 App 功能设计稿，测试期间只读，见 [使用说明](docs/UIUX知识库.md)；
知识卡与路径图保存实际测试经验，见 [维护说明](docs/知识卡与路径图.md)。

## 快速开始

### 一键安装（推荐）

```powershell
pwsh -File scripts/setup.ps1
```

脚本会依次：检查 adb → 检查设备 → 建 venv 装依赖 → 初始化 uiautomator2 → 自检。

常用参数：

```powershell
pwsh -File scripts/setup.ps1 -SkipDeviceCheck    # 没插设备也先装依赖
pwsh -File scripts/setup.ps1 -Recreate           # 重建已存在的 venv
pwsh -File scripts/setup.ps1 -Python "C:\Python310\python.exe"   # 指定解释器
```

> **Python 版本要求：3.10 ~ 3.12**
>
> - **3.9 不行**：`pillow` 12 起要求 `>=3.10`
> - **3.13+ 不行**：`rapidocr-onnxruntime` 要求 `<3.13`，装了会直接失败
> - 3.10 上各依赖均有可用版本；脚本会自动挑出符合要求的解释器

### 手动安装

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
adb devices -l                              # 设备在线且已授权
.venv\Scripts\python -m uiautomator2 init   # 设备端初始化（每台设备一次）

# 看一眼设备当前画面
.venv\Scripts\python tools\observe.py --name smoke/first

# 之后交给 AI：把用例口述给它，它按 SKILL.md 的工作流执行
```

先 `session.py start` 开会话，再显式完成环境准备并执行正式步骤，准备过程也记入本次测试。文件准备、数据清理、权限和前提规则见 [执行前设备环境准备](docs/执行前设备环境准备.md)。

启动测试台：

```powershell
.venv\Scripts\python webui.py               # http://127.0.0.1:9810
```

> **改过 `scripts/*.ps1` 后跑一次 BOM 校验**：Windows PowerShell 5.1 读无 BOM 的
> `.ps1` 会按 GBK 解析，中文/emoji 会导致语法崩溃。多数编辑工具重写文件时会
> 丢掉 BOM，所以改完必查：
> ```powershell
> pwsh -File scripts/check_bom.ps1        # 只看；-Fix 自动补回
> ```

## 工具层（无流程逻辑，每个都是独立命令）

| 命令 | 作用 |
|---|---|
| `tools/observe.py` | dump UI 树（摘要节点列表）+ 截图 + 前台包名/activity/旋转 |
| `tools/act.py` | tap / longclick / input / swipe / back / home / key；`--via` 溯源、`--why` 理由、`--watch` 瞬态弹窗响应、`--settle` 稳定窗口 |
| `tools/read.py` | OCR 读 toast / Canvas 自绘文字（输出像素 + 归一化坐标） |
| `tools/prepare/` | 执行前准备入口：sdcard init/clear 准备设备文件，grant-all 批量授权；结果记入当前会话 |
| `tools/state.py` | App 数据清理、单项运行时权限授予与撤销，以及应用启停 |
| `tools/session.py` | 会话生命周期：start / pause(--ask 问人) / resume / finding / finish；case 用例库；paths / paths-apply 路径图草稿采集与应用 |
| `tools/logcat.py` | 崩溃/ANR 取证：分级（被测/关联/无关）、自动抓崩溃前 20s 日志 |
| `tools/vision.py` | 可选视觉通道：OpenAI 兼容多模态模型问图（测试台「视觉模型」页配置） |
| `tools/cleanup.py` | 证据/日志轮转（--days，防 storage 膨胀） |

所有 observe/act/read 调用自动归档证据到 `storage/evidence/`（`--name` 可省略，
自动派生 `<会话id>/step<N>`），并自动写入当前会话事件流。

## 测试会话与测试台

```powershell
.venv\Scripts\python tools\session.py start --title "冒烟" --input "口述的用例原文"
# …… AI 调 observe/act/read 执行（自动记录事件流）……
.venv\Scripts\python tools\session.py finish --status PASS --summary "全过"
.venv\Scripts\python webui.py        # http://127.0.0.1:8900 查看时间线/证据/知识库
```

数据库 `storage/sessions.db` 三张表：`sessions`（会话）/ `events`（工具调用事件流，
自动写入）/ `findings`（断言结论）。界面按"会话 → 时间线 → 截图证据"组织。

## 目录

```
├── SKILL.md         # 工具说明书（AI 按需加载）
├── tools/           # 薄工具层
│   └── prepare/    # 文件准备与批量授权，python tools/prepare 调用
├── media-resources/ # 会话准备使用的图片和视频
├── uiux/            # 测试期间只读；按包名组织的 UIUX 页面、局部图及来源
├── knowledge/       # App 知识卡（按包名，按交互类型组织）
├── webui/           # 测试台前端（会话时间线 / 知识库编辑）
├── webui.py         # 测试台服务（标准库，零依赖）
└── storage/         # 运行产物：evidence/ 证据、sessions.db 记录
```
