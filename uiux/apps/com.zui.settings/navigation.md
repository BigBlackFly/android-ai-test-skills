# 页面导航与状态依赖

[App 索引](README.md) · [功能意图索引](functions.md)

本表用于从当前页面规划下一步；不是固定点击脚本。上级文档包含入口外观，目标文档包含到达确认和状态条件。若已经到达中间节点，从该节点继续；若用例规定入口，遵循用例。

## 起点 → 入口 → 目标

| 当前页面／起点 | 要找的入口与操作 | 目标资料 |
|---|---|---|
| [设置首页](pages/home/README.md) | 关于平板电脑 | [关于平板电脑](pages/about/README.md) |
| [设置首页](pages/home/README.md) | 账号卡片／账号和服务／账号和同步 | [账号和服务／账号和同步](pages/accounts/README.md) |
| [设置首页](pages/home/README.md) | 高级功能 → 实验室功能（按任务需要） | [高级功能与实验室](pages/advanced/README.md) |
| [设置首页](pages/home/README.md) | PRC：AI 智慧服务 | [AI 智慧服务](pages/ai_services/README.md) |
| [应用管理](pages/app_management/README.md) | 应用分身（PRC） | [应用分身](pages/app_clone/README.md) |
| [应用管理](pages/app_management/README.md) | 所有应用 → 目标应用 | [应用信息](pages/app_info/README.md) |
| [设置首页](pages/home/README.md) | 应用管理 | [应用管理](pages/app_management/README.md) |
| [声音和振动](pages/sound/README.md) | 背景音 | [背景音（仅入口存在时）](pages/background_sound/README.md) |
| [通用设置](pages/general/README.md) | 备份 | [备份](pages/backup/README.md) |
| [显示和亮度](pages/display/README.md) | 自动切换 | [深浅色自动切换](pages/dark_mode/README.md) |
| [通用设置](pages/general/README.md) | 日期和时间 | [日期和时间](pages/date_time/README.md) |
| [应用管理](pages/app_management/README.md) | 默认应用 | [默认应用](pages/default_apps/README.md) |
| [设置首页](pages/home/README.md) | 显示和亮度 | [显示和亮度](pages/display/README.md) |
| [显示和亮度](pages/display/README.md) | 显示大小和文字 | [显示大小和文字](pages/display_size_text/README.md) |
| [声音和振动](pages/sound/README.md) | 杜比全景声／杜比音效 | [杜比音效](pages/dolby/README.md) |
| [显示和亮度](pages/display/README.md) | 护眼模式 | [护眼模式](pages/eye_comfort/README.md) |
| [设置首页](pages/home/README.md) | 通用设置 | [通用设置](pages/general/README.md) |
| 已识别的系统设置App | 系统设置／设置 | [设置首页](pages/home/README.md) |
| [显示和亮度](pages/display/README.md) | 界面材质 | [界面材质](pages/interface_material/README.md) |
| [通用设置](pages/general/README.md) | 键盘 | [键盘、输入法与鼠标](pages/keyboard/README.md) |
| [通用设置](pages/general/README.md) | 语言 | [语言](pages/language/README.md) |
| [关于平板电脑](pages/about/README.md) | 法律信息／监管信息 | [法律与监管信息](pages/legal/README.md) |
| [设置首页](pages/home/README.md) | 位置信息 | [位置信息](pages/location/README.md) |
| [声音和振动](pages/sound/README.md) | 模式 → 勿扰／睡眠 | [模式与勿扰](pages/modes/README.md) |
| [通用设置](pages/general/README.md) | 多用户（ROW） | [多用户](pages/multi_user/README.md) |
| [设置首页](pages/home/README.md) | 通知和控制中心 | [通知和控制中心](pages/notifications/README.md) |
| [高级功能与实验室](pages/advanced/README.md) | ROW：实验室内智能常亮／靠近亮屏／距离提醒 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) |
| [设置首页](pages/home/README.md) | PRC：隐私保护；ROW：安全和隐私内的隐私入口 | [隐私保护／隐私控制](pages/privacy/README.md) |
| [显示和亮度](pages/display/README.md) | 阅读模式 | [阅读模式](pages/reading_mode/README.md) |
| [显示和亮度](pages/display/README.md) | 屏幕刷新率 | [屏幕刷新率](pages/refresh_rate/README.md) |
| [通用设置](pages/general/README.md) | 重置选项 | [重置选项](pages/reset/README.md) |
| [声音和振动](pages/sound/README.md) | 通知铃声／任务指定的铃声行 | [铃声选择](pages/ringtones/README.md) |
| [设置首页](pages/home/README.md) | 安全／安全和隐私／安全和紧急情况 | [安全、隐私与紧急情况](pages/safety/README.md) |
| [通用设置](pages/general/README.md) | 定时开关机 | [定时开关机](pages/scheduled_power/README.md) |
| [显示和亮度](pages/display/README.md) | 屏幕色调 | [屏幕色调](pages/screen_color/README.md) |
| [显示和亮度](pages/display/README.md) | 屏幕熄灭时间 | [屏幕熄灭时间](pages/screen_timeout/README.md) |
| [设置首页](pages/home/README.md) | 搜索框 | [设置搜索](pages/search/README.md) |
| [设置首页](pages/home/README.md) | 声音和振动／声音 | [声音和振动](pages/sound/README.md) |
| [关于平板电脑](pages/about/README.md) | 状态信息 | [状态信息](pages/status/README.md) |
| [通用设置](pages/general/README.md) | 存储 | [存储](pages/storage/README.md) |
| [设置首页](pages/home/README.md) | 手写笔和键盘 | [手写笔和键盘](pages/stylus_keyboard/README.md) |
| [声音和振动](pages/sound/README.md) | 振动和触感反馈 | [振动设置](pages/vibration/README.md) |

## 路径中的特殊分支

| 条件／目标 | 需要保留的中间步骤 |
|---|---|
| 查系统应用详情 | 应用管理 → 所有应用 → 右上三点更多 → 显示系统程序／应用 → 目标应用；文字以当前菜单为准 |
| 设置图片／文档默认应用 | 应用管理 → 默认应用 → 更多默认应用 → 文件类别 → 候选应用；若出现确认框，处理后核对选择 |
| ROW感知功能 | 高级功能 → 实验室 → 智能常亮／靠近亮屏／距离提醒 |
| PRC距离提醒 | 学习助手 → 健康护眼 → 距离提醒；前两层缺完整布局，不使用ROW实验室图定位 |
| ROW部分AI服务 | 高级功能 → 实验室 → 实际出现的AI服务；并非PRC所有服务都存在 |
| ROW隐私 | 安全和隐私 → 实际提供的隐私入口；具体条目以实机核对 |
| 键盘硬件模块缺失 | 通用设置 → 键盘，处理系统键盘任务；不能用此路径代替手写笔配对测试 |

## 搜索作为备选路径

用例允许时，从[首页搜索框](pages/home/README.md)进入[搜索](pages/search/README.md)，输入实际功能名称，核对结果标题与路径，点击后核对目标页。搜索索引范围未完整提供；无结果不能推出功能不存在。一次性高亮会消退，不作为必须持续存在的到达标志。

## 返回与跨 App

推荐操作策略：当前有弹窗先处理弹窗；再使用当前可见返回入口或系统返回并检查实际结果。搜索入口和普通层级可能有不同返回栈。返回不等于保存，是否生效以目标页反馈为准。跨App后重新识别包名和页面，不沿用设置页控件定位。

## 非线性跳转和联动

| 起点／触发 | 目标或结果 | 条件与加载 |
|---|---|---|
| 首页搜索 → 结果 | 目标页面及高亮项 | [搜索](./pages/search/README.md)；退出保留原页面 |
| 自动外观计划 → 缺定位提示 | 位置设置／授权 | [自动切换](./pages/dark_mode/README.md)、[位置](./pages/location/README.md) |
| ROW 位置时区 → 位置关闭 | 位置设置提示 | [日期和时间](./pages/date_time/README.md) |
| 控制中心静音／振动／收音 | 设置状态同步 | [同步关系](./features/control_center_sync/README.md) |
| 锁屏通知从两个入口修改 | 同一偏好 | [隐私](./pages/privacy/README.md)、[通知](./pages/notifications/README.md) |
| 阅读省电／全局手写笔 | 刷新率限制 | [阅读](./pages/reading_mode/README.md)、[刷新率](./pages/refresh_rate/README.md) |
| 开发者选项隐藏长时熄屏档位 | 可能恢复默认时长 | [熄屏时间](./pages/screen_timeout/README.md) |
| 连接外接显示器 | 常亮／靠近／距离项禁用，点击解释 | [感知功能](./pages/presence/README.md) |
| KidsSpace 一次性提醒 | 不用了继续；前往设置去距离提醒 | PRC／ROW 路径不同，见[感知功能](./pages/presence/README.md) |
| 应用列表更多 → 重置应用偏好 | 确认页 | [应用管理](./pages/app_management/README.md)、[重置](./pages/reset/README.md) |
| 新建用户后取消切换 | 留在当前用户，新用户仍存在 | [多用户](./pages/multi_user/README.md) |
| 想帮帮恢复桌面图标 | 按钮变打开，再点击启动 | [AI 服务](./pages/ai_services/README.md) |

## 跨 App 边界

安全中心、联想闪传、联想云／Google、Lenovo ID、文件管理以及各 AI 服务的目标 UI 未全部提供。当前资料只能确认设计中声明的跳转；到达后需再按目标包名发现其知识库。图库不是本包内容，但用户选择头像或音频等流程可能触发系统选择器或其他 App，不能直接假定一定是图库。
