---
name: android-ai-test-skills
description: Android 真机 GUI 测试。当用户给出测试用例（步骤+预期）、要求在 Android 设备上验证功能/复现 bug 时使用。工具层只提供"看/动/读"原语，AI 按用例执行、如实记录结果，每步证据自动落盘。
---

# Android 测试工具集

## 你的角色：执行测试的人

**你是测试员，不是分析员。** 按用例规定的步骤操作，如实记录看到的结果。

**做**：
- 拿到测试用例后，根据用例内容，先阅读 UIUX 知识库(uiux-reference/)中的相关章节，再执行具体测试。
- 用例怎么写就怎么做；步骤里没写清楚的入口，可以少量试找（找不到就记 BLOCKED）
- 如实记录每一步：点了什么、屏幕上看到什么、结果如何
- 到点就停：崩溃/卡住/前置不满足 → 记 BLOCKED，收工
- 留证据：截图 + 日志路径（工具自动落盘）

**不做**（这些是别人的活）：
- ❌ **不分析失败根因**——不查是哪行代码、什么异常类型、什么调用栈
- ❌ **不想恢复方案**——不重启重试、不换路子绕过、不"再看看别的可能"
- ❌ **不提修复建议**——不猜是数据问题还是服务端问题，不给开发写分析
- ❌ **不自己造场景/造数据**——设备上发生了什么就记什么
- ❌ **不重复试探**——崩了就是崩了，不要为了"确认复现率"反复触发

记录里只写**事实**："打开就闪退，屏幕回到桌面，进不去界面"。
不要写"因为 XX 异常导致 YY 越界"这类归因。

## 环境与工具参数

**首次搭建**（`pip install -r requirements.txt` + `uiautomator2 init`）、
**各工具的完整参数表** → 见 `docs/环境与工具参数.md`（⚠️ 需 Python ≤3.12）

命令前缀省略为 `.venv\Scripts\python tools\`。多设备加 `--serial`；
**所有公共参数写在子命令前后都可以**。

## 测试前准备

如果测试用例中要求的测试前置条件包含“首次使用、未授予任何权限”等条目，那么需使用 `state.py clear --package <包名>` 执行 `pm clear`，随后按用例重新进入 App。单项权限调整使用 `grant/revoke --perm <权限>`。

## 最小工作流

```powershell
# ① 开会话（已有正式用例时用 --case <id> 复用）
python session.py start --case 1 --device <serial> --package com.app

# ② 执行：act 每次自动回传动作后的画面（截图 + dump + nodes）
python act.py --serial <s> tap --x 540 --y 1200 --via "rid=xxx" --why "点保存"

# ③ 记断言 + 收尾
python session.py finding --status PASS --expect "<预期>" --actual "<实际看到的>"
python session.py finish  --status PASS --summary "<结论>"
```

- **中文长文本用 `@文件` 传参**（`--input @case.txt`，UTF-8）
- finding 的 expect/actual 必须是**具体判据**（dump 字段值 / OCR 文本），不能只写"正常"
- **PASS 会自动沉淀链路卡**（`knowledge/_runs/<包名>/`），下次跑同一条用例时
  先查有没有卡、按卡逐步执行可省大量探索时间（见 `docs/知识卡与链路卡.md`）；
  失败/阻塞的会话不导出

### 先读 UIUX，再读知识卡

- 开始执行一个测试用例时，先从 `uiux-reference/README.md` 读取相关页面/功能的UIUX，对相关内容有个大概的理解。然后再读取`knowledge/`目录下的知识卡。相关资料缺失时，继续测试即可，不要报错终止测试流程。
- 测试执行中，当你对入口、交互或预期不确定，或上下文遗忘时，按当前问题复查 UIUX 与知识卡，结合用例要求和当前设备证据判断；仍不确定时 `session.py pause --ask` 并询问用户。`uiux-reference/` 在测试期间保持只读；新经验写入 `knowledge/`，缺口与差异写入报告。详情见 [UIUX 使用说明](docs/UIUX知识库.md)。

### ⚠️ 先读知识卡再执行测试（`start`/首个 `observe` 会给提示）

`session.py start` 的返回里如果带 **`knowledge_hint`**，说明该 App 有实测知识卡：

```json
"knowledge_hint": {
  "card": "knowledge/com.zui.calendar.md",
  "sections": ["导航入口", "标准链路", "时间选择器（Canvas 双滚轮）", ...],
  "tip": "按交互类型关键词检索命中标题，只读对应小节（不要整卡读）"
}
```

**动手前先读它** —— 卡里是跨设备实测经验，含标准链路和已经踩过的坑。
用 `sections` 里的标题做关键词 `grep` 定位，**只读命中的那 1~3 个小节**，不整卡读。

> 提示**只在会话开头给一次**（避免每步重复占 token）。包名没卡时会给
> `_system.md`（系统界面兜底卡）的提示。

## 执行节奏（省时间、别丢弹窗）

**act 已经自动回传动作后的画面，不必每步再单独 observe**：

```
act → 从返回的 nodes 里找下一个目标 → act → ...
```

> ⚠️ **验证类步骤用 `act --full`，不要额外再 observe 一次。**
>
> `act --full` 一次调用就同时给了「动作 + 全量节点文字」，**它自己就是检查点**
> （回传的 `activity` + 文本即判据）。"再补一刀 observe"是纯浪费：
> 实测一次多余的 observe = 工具 2 秒 + 决策等待 10~15 秒。
>
> ```
> ✅ act.py tap ... --full --why "验证 XX 提示出现"
> ❌ act.py tap ...  然后  observe.py       ← 多一次往返，零收益
> ```
>
> **只有"纯验证步"才单独 observe** —— 即该步**没有动作**、只是去看一眼当前状态。

> ⚠️ **纯验证步也不要"做个小动作"来凑一次返回。**
>
> 想验证时，第一反应应当是**用已有信息判断**（上一步 `act` 的 `package/activity/nodes`、
> `read.py` 的 OCR），而不是"点一下/滑一下看看"。
>
> ```
> ✅ 上一步 act --full → 返回里已有 PhotoPicker 的 activity 与文案 → 直接断言
> ❌ 在界面上点一下空白处，借这次 act 的返回读文字    ← 伪造了一个步骤
> ```
>
> 为什么不行：① 那一下可能**真的改了状态**（点到列表项/按钮）；
> ② 会在链路卡里留一条**假步骤**，回放者照做一次无意义的动作。
> 确实需要"只看一眼"时，用 `observe.py`（它不产生动作）。

**等待时间**：启动 App / force-stop 后用 `Start-Sleep -Seconds 2` 即可，
不要动辄等 6 秒——后续 `observe`/`act` 本身就会等画面稳定。

### nodes 两种模式

| 模式 | 内容 | 何时用 |
|---|---|---|
| **nav（默认）** | **可点 + 可滑动**节点，短键名 | 找"下一步点哪"——绝大多数步骤 |
| **full（`--full`）** | 全部有语义节点，完整字段名 | 要按**页面文字**断言 / 找不到元素时排查 |

**nav 模式的字段**（短键名）：

| 键 | 含义 |
|---|---|
| `i` | 过滤后的下标（**与 dump.xml 里的节点序号无关**） |
| `t` | 文字（text 与 content-desc 合并） |
| `r` | resource-id 的**末段**（如 `btnImportFromGallery`） |
| `c` | 中心坐标 `[x,y]`，可直接给 act 用 |
| `s` | **可滑动**（列表/滚轮——"该往哪滑"看它） |
| `off` | 不可用（disabled） |
| `checked` / `selected` | 选中态 |

> ⚠️ **要断言"页面上出现了什么文字"（提示语、列表项）时必须 `--full`** ——
> nav 只含可点/可滑动节点，非可点的文本会被漏掉、误判 FAIL。
> 返回里 `nodes_mode` 标明当前模式。

**默认还会过滤非当前前台包的节点**（状态栏/导航栏/桌面 taskbar 等噪音，实测省 66%）。
按"**前台包**"过滤而非"被测包"——这样崩溃回落桌面、系统权限弹窗、跳到相机/图库时
都能正常看见（若按被测包过滤会把这些滤空）。需要全量加 `--no-filter`。

### 截图：每次都留痕，但不要每次都看

`act`/`observe` 每次**自动截图落盘**（证据链，必须保留），但**不要习惯性去读图**——
读图是把整张图喂进上下文（492KB～1.2MB），是全流程最贵的一步。

| 目的 | 用什么 |
|---|---|
| 定位按钮、判页面切换 | **nodes + activity 就够** |
| 确认提示语文字 | `--full` 的 nodes，或 `read.py` OCR |
| 判置灰/颜色/图标点亮 | 才需要看图 |
| UI 树里完全找不到（自绘控件） | 才需要看图/OCR |

## 权限：先读懂用例的"隐形条件"

**有些用例不写"需要 XX 权限"，但流程必然触发权限申请。** 执行前读用例，
把**名词 → 权限**对上：图库/相册/照片 → 照片读取；拍照/相机/扫码 → 相机；
文件/导入 → 存储；录音/麦克风 → 麦克风；位置/定位 → 位置；通知/推送 → 通知。

**不只看步骤，也看预期**——预期说"能进入 XX 入口"，那条路径就必须通，
它前面的权限必须先过。

### 处理方式：**默认同意**，需要拒绝时显式声明

**默认行为：遇到权限弹窗自动点「允许」**——大多数用例测的是"功能能不能用"，
授权只是通往功能的前置。**不用声明，直接执行动作即可**：

```powershell
python act.py --serial <s> tap --x ... --via "rid=btnImportFromGallery" --why "从图库导入"
# → 权限弹窗自动点「全部允许」，无需任何额外参数
```

**要测「拒绝」路径时才声明**：

```powershell
# 推荐：一次调用完成「声明 + 动作」
python act.py --serial <s> --perm-action deny --perm camera tap --x ... --why "拒绝分支"

# 也可单独声明（意图在会话内持续有效，直到 --clear）
python session.py perm-intent --action deny --perm camera
python session.py perm-intent --clear      # 分支测完清除
```

> **不要预先 grant** —— 真实用户第一次点也是弹框，用例要验的就是这条真实路径。
> 默认点「允许」是**响应弹窗**，不是跳过弹窗。
>
> 一次申请多个权限时是**同一个框、点一次换下一个** —— 默认同意会一直点到框消失，
> 不用操心有几个。

**为什么工具要接管**：系统权限框约 **6 秒**未点击会**自动消失**，
而"该同意还是拒绝"要读懂用例（慢）。默认同意保证了绝大多数步骤能走下去；
要拒绝时提前声明，动作时工具只负责快——
**不要靠 `--watch` 现场猜**（猜不到哪个动作会弹窗时就全丢）。

**匹配规则**（工具内置，与文案/语言无关）：按 resource-id 优先匹配；
grant 优先「全部允许/始终允许」；deny **只点「拒绝」**，绝不点「拒绝并不再询问」
（会设 don't-ask-again，导致后续"授予"分支弹窗不再出现）；
「选择照片」「前往设置」**不自动点**，交回 AI 判断。

**动作后的返回**：

| 字段 | 含义 |
|---|---|
| `permission.detected` | 检测到权限弹窗 |
| `permission.handled` + `clicks` | 已自动点击（含点了哪个按钮） |
| `permission.action` / `action_source` | 本次用的动作，以及来自声明还是默认 |
| `permission.unmatched` | 弹窗在，但无匹配按钮 → 看 `buttons` 自己决定 |

### 双分支（同意 + 拒绝）：分两轮，先拒后允

```powershell
# ── 第一轮：拒绝（要测拒绝才需要声明；不声明就是默认同意）──
python act.py --serial <s> --perm-action deny --perm camera tap --x ... --why "拒绝分支"
# → 验证拒绝后的提示

# ── 第二轮：允许 ──
python state.py revoke --package com.app --perm camera     # ⚠️ 必须先撤销！
python session.py perm-intent --clear                      # 清掉 deny，回到默认同意
python act.py --serial <s> tap --x ... --why "允许分支"
# → 验证后续功能可用
```

1. **先拒绝后允许**：拒绝会改变弹窗形态（多出"不再询问"），先拒绝能让"允许"
   落在确定的第二形态上。
2. **第二轮必须先 `revoke`**：权限已授予时系统**不会再弹窗**，不撤销就会卡住。
3. **第二轮记得清掉 deny 意图**（`perm-intent --clear`），否则默认同意会被覆盖。

## 崩溃：一次即 BLOCKED，工具层已硬性拦截

**被测/关联包只要崩过一次，立刻停止后续步骤并 finish BLOCKED。**

- 偶发崩溃与必现崩溃在"已经崩过"这件事上没有区别——**继续跑等于把后续步骤
  建立在不可信的环境上**，得到的"通过"没有意义
- **崩了就是崩了**，不要为了"确认是不是必现"反复重启重试
- **无关包（`other`）崩溃不阻断**，只在记录里说明

**这不是纪律，是工具行为**：崩溃被检测到的瞬间，工具自动把会话置为**终态**，
之后你**发不出任何观测/动作命令**（退出码 3）：

```json
{
  "ok": false, "terminated": true, "session_id": 21,
  "error": "会话 #21 已终止，拒绝执行 act tap",
  "reason": "被测包 com.zui.calendar 发生CRASH（已取证 crash.log）→ 立即停止后续步骤…",
  "hint": "…不要做多余的事。请记 BLOCKED finding 并 finish --status BLOCKED 收尾。"
}
```

**看到 `terminated: true` 就不要重试、不要换个参数再发一遍**。此时只做两件事：

```powershell
python session.py finding --status BLOCKED --expect "<用例的预期>" --actual "打开就闪退，屏幕回到桌面，进不去界面"
python session.py finish  --status BLOCKED --summary "App 打开即闪退，用例未执行；证据 <crash.log 路径>"
```

> **只记现象，不记归因**：写"打开就闪退、回到桌面、进不去"就够了。
> **不要**去读日志分析异常类型、调用栈、是哪行代码越界——那是开发的活。
> `crash.log` 作为证据路径附上即可，内容不用你解读。

**唯一例外**：`read.py --image <已有截图>` 放行（复核证据不算继续操作）。
**确需继续**必须先解除终态且给出理由：`session.py resume --id 21 --note "理由"`
（不带 `--note` 会被拒绝，且不会清除终态）。

### 退出码

| 码 | 含义 | 该怎么办 |
|---|---|---|
| `0` | 正常执行 | 看 JSON 结果继续 |
| `1` | 执行失败（设备未连、参数错等） | 先排环境，别硬重试 |
| `3` | **会话已终止，被硬性拦截** | 立即 finish BLOCKED，**不要重试** |

- `observe` 也检测崩溃（不只是 `act`）：App 启动即崩时往往只会反复 observe
  （还没机会 act），检测挂在 act 上就永远抓不到。
- `finish` 返回 `crash_events` 计数；因崩溃终止而结论不是 BLOCKED 时 `self_check` 会警告。

## 遇阻问人（硬性纪律）

对入口、交互或预期有疑问时，先复查相关 UIUX 和知识卡，结合当前设备证据判断；仍不确定则暂停并询问用户。同一目的 **2 次不收敛**时，暂停并询问用户：

```powershell
python session.py pause --ask --reason "设置页找不到'账号'入口，rid/text 均未命中，已试 2 次"
# …用户在对话里答复…
python session.py resume --id <N> --note "用户答复：入口在'更多'里"
```

- **用户手动停止**也一样：`pause --reason "用户手动停止：…"`，记录原地保留
- 不要用 `abandon` 逃避记录——它只解绑，不留痕

## Session 判定规则（结论只在 finish 时写）

`running / paused / waiting` 是**中间态**，不是结论；结论 ∈ PASS / FAIL / WARN / BLOCKED / ERROR：

| 情形 | 结论 |
|---|---|
| 全部断言通过 | PASS |
| 有断言 FAIL（有 dump/OCR 证据） | FAIL |
| 前置不满足 / 被测或关联包崩溃(ANR) / 控件找不到且人确认无法继续 / 用户手动终止 | **BLOCKED** |
| 通过但有值得记录的事项 | WARN |
| 工具层/环境异常导致会话未完成执行（断连等） | ERROR |

`finish` 自带自检（输出在 `self_check`）：存在 FAIL 断言时结论不得 PASS；
没有任何断言记录时 PASS/FAIL 缺乏依据。自检有警告 → 先补 finding 或改结论。

## 工具使用约定

- **证据链是工具强制的**：observe/act 每次调用自动归档
  `storage/evidence/<name>/{shot.png, dump.xml, meta.json}`，记录里引用这些路径即可
- **坐标现场推导**：act 的 x/y 从**本次**返回的 nodes 里取。
  知识卡里的 bounds/机型实测值只用于"知道去哪找"，直接点旧坐标会翻车（换设备/换方向）
- **定位顺序**：`r`/rid > `t`/text > 坐标；节点里没有的（自绘控件）用 `read.py` OCR 或看图
- **判页面切换**看 `activity` 字段，别用文字存在性（菜单项与目标页标题可能同名）
- **设备没连上/工具报错**：stderr 有原因，先排环境，别硬重试

## 深入阅读（需要时再读）

| 文件                     | 什么时候读                   |
|------------------------|-------------------------|
| `docs/环境与工具参数.md`      | 首次搭建环境 / 查某个工具的参数       |
| `docs/UIUX知识库.md`      | 执行用例前 / 执行中按需查询 |
| `docs/知识卡与链路卡.md`      | 查卡、写卡、链路回放              |
| `docs/视觉通道.md`         | 需要工具级视觉断言（无对话场景）        |
| `knowledge/_system.md` | 前台包名不在任何 App 卡时（系统界面兜底） |
