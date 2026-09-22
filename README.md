# android-ai-test-skills

Android 设备黑盒 GUI 测试 v2：**AI 即执行者**。

对话里的 AI（CodeBuddy / Claude Code）直接驱动真机执行测试用例：每步调用薄工具层
"看（observe）/ 动（act）/ 读（read）"，自行分析结果、规划下一步；知识卡承载 App
操作经验；每步证据自动落盘，最终输出带证据的测试报告。

与 v1（AI 写 Python 用例脚本 → 确定性回放）的区别：**不再写 case**。
用例就是用户口述的步骤+预期，执行即探索，成功路径的知识沉淀进知识卡/
链路卡而不是代码。v1 框架时期的日历链路源码已归档至
`knowledge/_runs/com.zui.calendar/_v1_flow_reference.py` 供参考。

## 快速开始

```powershell
# 1. 环境（一次）
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
adb devices -l                              # 设备在线且已授权
.venv\Scripts\python -m uiautomator2 init   # 设备端初始化（每台设备一次）

# 2. 看一眼设备当前画面
.venv\Scripts\python tools\observe.py --name smoke/first

# 3. 之后交给 AI：把用例口述给它，它按 SKILL.md 的工作流执行
```

## 工具层（无流程逻辑，每个都是独立命令）

| 命令 | 作用 |
|---|---|
| `tools/observe.py` | dump UI 树（摘要节点列表）+ 截图 + 前台包名/activity/旋转 |
| `tools/act.py` | tap / longclick / input / swipe / back / home / key；`--via` 溯源、`--why` 理由、`--watch` 瞬态弹窗响应、`--settle` 稳定窗口 |
| `tools/read.py` | OCR 读 toast / Canvas 自绘文字（输出像素 + 归一化坐标） |
| `tools/state.py` | 设备状态原语：权限 grant/revoke、pm clear、应用启停 |
| `tools/session.py` | 会话生命周期：start / pause(--ask 问人) / resume / finding / finish / export 链路卡 |
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
├── SKILL.md        # 工具说明书（AI 按需加载）
├── tools/          # 薄工具层：observe / act / read / session + db
├── knowledge/      # App 知识卡（按包名，按交互类型组织）
├── webui/          # 测试台前端（会话时间线 / 知识库编辑）
├── webui.py        # 测试台服务（标准库，零依赖）
└── storage/        # 运行产物：evidence/ 证据、sessions.db 记录
```
