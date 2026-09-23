# 系统设置：功能入口与页面索引

[全库入口](../../README.md) · [按功能查找](./functions.md) · [页面导航](./navigation.md)

App ID：`settings`。应用名称：系统设置。包名：`com.zui.settings`（项目指定）。运行时仍核对设备上的实际包名和版本。

## 查资料方式

优先读[功能意图索引](functions.md)，匹配用例的说法，再读目标页的“进入本页”。入口定位失败时读该页排查顺序；仅跨页依赖或规划路径时读[导航](navigation.md)。当前收录 42 个页面／页面组及 5 个跨页专题；页面组内的小弹窗和紧密相关子页放在同一文档。

## 执行测试用例之前需要了解的公共常识

| 情况 | 对操作的影响 |
|---|---|
| 双栏 | 一级入口在左侧导航；子功能在右侧内容。滚动目标所属区域，点击后核对右侧标题 |
| 单栏／分屏切换 | 进入模块可能切整页；窗口尺寸变化后重新获取截图和控件树 |
| 入口行与开关 | 带箭头的行通常进入子页；胶囊开关直接切换状态。不能仅按颜色判断开启或禁用 |
| PRC／ROW | 分别指中国区／其他地区设计分支；按实际可见布局和设备配置选择，不要求运行时一定能读到该英文标记 |
| LTE／Wi-Fi、外设、父开关 | 决定部分条目是否存在或可操作；具体条件读页面说明 |
| 跨 App 跳转 | 安全中心、账号、云服务、文件选择等可能离开设置；以实际包名与标题识别目标后加载相应 App 资料 |
| 测试依据 | 原图说明设计预期；当前界面说明实际状态。资料与界面不符要记录差异，不能据此自动宣布通过或失败 |

## 覆盖边界

网络连接、账号登录、备份恢复、部分权限与子服务只有入口或局部信息。找到入口不代表本包已描述完整功能流程；见[功能覆盖表](functions.md)及各页“资料覆盖”。没有证据的控件语义、路径或保存行为不补造。

## 页面入口

| 知识 ID | 页面 | 入口 |
|---|---|---|
| `settings.home` | [设置首页](./pages/home/README.md) | 启动设置 |
| `settings.search` | [设置搜索](./pages/search/README.md) | 设置首页 > 搜索框 |
| `settings.display` | [显示和亮度](./pages/display/README.md) | 设置 > 显示和亮度 |
| `settings.dark_mode` | [深浅色自动切换](./pages/dark_mode/README.md) | 设置 > 显示和亮度 > 自动切换 |
| `settings.screen_color` | [屏幕色调](./pages/screen_color/README.md) | 设置 > 显示和亮度 > 屏幕色调 |
| `settings.refresh_rate` | [屏幕刷新率](./pages/refresh_rate/README.md) | 设置 > 显示和亮度 > 屏幕刷新率 |
| `settings.eye_comfort` | [护眼模式](./pages/eye_comfort/README.md) | 设置 > 显示和亮度 > 护眼模式 |
| `settings.reading_mode` | [阅读模式](./pages/reading_mode/README.md) | 设置 > 显示和亮度 > 阅读模式 |
| `settings.screen_timeout` | [屏幕熄灭时间](./pages/screen_timeout/README.md) | 设置 > 显示和亮度 > 屏幕熄灭时间 |
| `settings.display_size_text` | [显示大小和文字](./pages/display_size_text/README.md) | 设置 > 显示和亮度 > 显示大小和文字 |
| `settings.interface_material` | [界面材质](./pages/interface_material/README.md) | 设置 > 显示和亮度 > 界面材质 |
| `settings.sound` | [声音和振动](./pages/sound/README.md) | 设置 > 声音和振动（无振动硬件时为声音） |
| `settings.vibration` | [振动设置](./pages/vibration/README.md) | 设置 > 声音和振动 > 振动和触感反馈 |
| `settings.dolby` | [杜比音效](./pages/dolby/README.md) | 设置 > 声音和振动 > 杜比全景声／杜比音效 |
| `settings.ringtones` | [铃声选择](./pages/ringtones/README.md) | 设置 > 声音和振动 > 通知铃声／其他铃声入口 |
| `settings.modes` | [模式与勿扰](./pages/modes/README.md) | 设置 > 声音和振动 > 模式 > 勿扰／睡眠 |
| `settings.background_sound` | [背景音（仅入口存在时）](./pages/background_sound/README.md) | 设置 > 声音和振动 > 背景音 |
| `settings.notifications` | [通知和控制中心](./pages/notifications/README.md) | 设置 > 通知和控制中心 |
| `settings.privacy` | [隐私保护／隐私控制](./pages/privacy/README.md) | PRC：设置 > 隐私保护；ROW：安全和隐私内相关入口 |
| `settings.location` | [位置信息](./pages/location/README.md) | 设置 > 位置信息 |
| `settings.safety` | [安全、隐私与紧急情况](./pages/safety/README.md) | PRC：设置 > 安全；ROW：安全和隐私／安全和紧急情况 |
| `settings.ai_services` | [AI 智慧服务](./pages/ai_services/README.md) | PRC：设置 > AI 智慧服务 |
| `settings.stylus_keyboard` | [手写笔和键盘](./pages/stylus_keyboard/README.md) | 设置 > 手写笔和键盘 |
| `settings.advanced` | [高级功能与实验室](./pages/advanced/README.md) | 设置 > 高级功能 > 实验室功能 |
| `settings.presence` | [智能常亮、靠近亮屏与距离提醒](./pages/presence/README.md) | 高级功能 > 实验室；PRC 距离提醒在学习助手 > 健康护眼 |
| `settings.app_management` | [应用管理](./pages/app_management/README.md) | 设置 > 应用管理 |
| `settings.app_info` | [应用信息](./pages/app_info/README.md) | 设置 > 应用管理 > 所有应用 > 目标应用 |
| `settings.app_clone` | [应用分身](./pages/app_clone/README.md) | PRC：设置 > 应用管理 > 应用分身 |
| `settings.default_apps` | [默认应用](./pages/default_apps/README.md) | 设置 > 应用管理 > 默认应用 |
| `settings.general` | [通用设置](./pages/general/README.md) | 设置 > 通用设置 |
| `settings.date_time` | [日期和时间](./pages/date_time/README.md) | 设置 > 通用设置 > 日期和时间 |
| `settings.scheduled_power` | [定时开关机](./pages/scheduled_power/README.md) | 设置 > 通用设置 > 定时开关机 |
| `settings.storage` | [存储](./pages/storage/README.md) | 设置 > 通用设置 > 存储 |
| `settings.backup` | [备份](./pages/backup/README.md) | 设置 > 通用设置 > 备份 |
| `settings.reset` | [重置选项](./pages/reset/README.md) | 设置 > 通用设置 > 重置选项 |
| `settings.language` | [语言](./pages/language/README.md) | 设置 > 通用设置 > 语言 |
| `settings.keyboard` | [键盘、输入法与鼠标](./pages/keyboard/README.md) | 设置 > 通用设置 > 键盘；鼠标入口按连接状态 |
| `settings.multi_user` | [多用户](./pages/multi_user/README.md) | ROW：设置 > 通用设置 > 多用户 |
| `settings.about` | [关于平板电脑](./pages/about/README.md) | 设置 > 关于平板电脑 |
| `settings.status` | [状态信息](./pages/status/README.md) | 设置 > 关于平板电脑 > 状态信息 |
| `settings.legal` | [法律与监管信息](./pages/legal/README.md) | 设置 > 关于平板电脑 > 法律信息／监管信息 |
| `settings.accounts` | [账号和服务／账号和同步](./pages/accounts/README.md) | PRC：设置 > 账号和服务；ROW：账号和同步 |

## 跨页面机制

| 专题 | 用途 |
|---|---|
| [设置自适应布局](./features/adaptive_layout/README.md) | 横屏 竖屏 双栏 单栏 小窗 分屏 屏幕尺寸 |
| [首页设置建议](./features/suggestions/README.md) | 建议 推荐 用户体验 壁纸 熄屏 移除 卡片 |
| [物理音量键与音量面板](./features/volume_panel/README.md) | 音量键 浮层 媒体 来电 通话 每应用音量 实时字幕 |
| [深浅模式桌面小组件](./features/dark_widget/README.md) | widget 桌面 小组件 深色 浅色 移除 |
| [控制中心及跨页状态同步](./features/control_center_sync/README.md) | 控制中心 同步 磁贴 状态 恢复 联动 |

## 只在需要时查看

[操作依据不足时的处理](./limitations.md) · [原图与来源映射](./sources.md)。
