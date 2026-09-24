# 功能意图索引

[App 索引](README.md) · [页面导航](navigation.md)

先匹配用例中的动作、对象和限制条件。下表的自然语言说法是检索别名，不保证与屏幕文字完全一致；点击文字以目标页“进入本页”为准。读取目标页即可获得控件图和操作反馈，不必先读所有页面。

## 容易混淆的测试意图

| 用例说法／歧义 | 如何选择资料 |
|---|---|
| 自动锁屏、休眠、熄屏时间 | 调整空闲熄屏计时看[屏幕熄灭时间](pages/screen_timeout/README.md)；设置密码、锁屏认证或灭屏后锁定延迟不能据此替代，相关完整流程未收录 |
| 常亮 | 延长计时看[熄屏时间](pages/screen_timeout/README.md)；检测注视保持亮屏看[智能常亮](pages/presence/README.md) |
| 夜间模式、黑白显示 | 定时深色看[自动切换](pages/dark_mode/README.md)；减蓝光看[护眼](pages/eye_comfort/README.md)；阅读黑白看[阅读模式](pages/reading_mode/README.md) |
| 默认打开方式 | 选默认角色／文件类型看[默认应用](pages/default_apps/README.md)；某个应用的默认打开设置入口看[应用信息](pages/app_info/README.md) |
| 关闭声音 | 静音、媒体、闹钟看[声音](pages/sound/README.md)；限制打扰规则看[模式](pages/modes/README.md)；震动看[振动](pages/vibration/README.md) |
| 字幕 | AI服务看[AI智慧服务](pages/ai_services/README.md)；ROW原生实时字幕线索看[音量浮层](features/volume_panel/README.md)，两者不混同 |
| 键盘 | 系统输入法看[键盘](pages/keyboard/README.md)；笔／实体键盘卡片看[手写笔和键盘](pages/stylus_keyboard/README.md) |
| 给图库／其他应用授权 | 设置内管理权限先看[应用信息](pages/app_info/README.md)；目标App内部功能需查该App资料 |
| 重置／清理 | [重置选项](pages/reset/README.md)区分网络、应用偏好、清除所有数据；[存储](pages/storage/README.md)区分释放空间与SD格式化，不合并这些操作 |

## 自然语言 → 页面与入口

| 测试意图／常见说法 | 目标资料 | 推荐入口路径 |
|---|---|---|
| 查看机型；系统版本；设备名称；系统更新 | [关于平板电脑](pages/about/README.md) | 设置 > 关于平板电脑 |
| 登录联想账号；添加账号；账号同步；查找平板 | [账号和服务／账号和同步](pages/accounts/README.md) | PRC：设置 > 账号和服务；ROW：账号和同步 |
| 实验室；观影免打扰；智能收音；应用内屏蔽通知；DC柔光 | [高级功能与实验室](pages/advanced/README.md) | 设置 > 高级功能 > 实验室功能 |
| AI字幕；智慧识屏；写作助手；恢复AI桌面图标 | [AI 智慧服务](pages/ai_services/README.md) | PRC：设置 > AI 智慧服务 |
| 应用多开；双开；创建分身；删除分身 | [应用分身](pages/app_clone/README.md) | PRC：设置 > 应用管理 > 应用分身 |
| 卸载应用；强行停止；应用权限；应用存储；应用通知；画中画 | [应用信息](pages/app_info/README.md) | 设置 > 应用管理 > 所有应用 > 目标应用 |
| 找所有应用；显示系统应用；应用排序；恢复预装应用 | [应用管理](pages/app_management/README.md) | 设置 > 应用管理 |
| 白噪音；环境音；背景音源 | [背景音（仅入口存在时）](pages/background_sound/README.md) | 设置 > 声音和振动 > 背景音 |
| 云备份；联想云备份；Google备份；查看备份时间 | [备份](pages/backup/README.md) | 设置 > 通用设置 > 备份 |
| 夜间自动深色；定时切换主题；日落后深色；白天浅色 | [深浅色自动切换](pages/dark_mode/README.md) | 设置 > 显示和亮度 > 自动切换 |
| 手动改时间；关闭自动时间；时区；24小时制 | [日期和时间](pages/date_time/README.md) | 设置 > 通用设置 > 日期和时间 |
| 默认浏览器；默认打开方式；默认看图应用；Word默认应用 | [默认应用](pages/default_apps/README.md) | 设置 > 应用管理 > 默认应用 |
| 调亮屏幕；自动亮度；切换深色外观；自动旋转；抬起亮屏 | [显示和亮度](pages/display/README.md) | 设置 > 显示和亮度 |
| 放大字体；调显示大小；粗体；恢复文字默认设置 | [显示大小和文字](pages/display_size_text/README.md) | 设置 > 显示和亮度 > 显示大小和文字 |
| 杜比；音效模式；均衡器；EQ；电影音效 | [杜比音效](pages/dolby/README.md) | 设置 > 声音和振动 > 杜比全景声／杜比音效 |
| 防蓝光；护眼定时；护眼强度；夜间护眼 | [护眼模式](pages/eye_comfort/README.md) | 设置 > 显示和亮度 > 护眼模式 |
| 系统导航；任务栏；快捷手势；截屏录屏；内存扩展；开发者选项 | [通用设置](pages/general/README.md) | 设置 > 通用设置 |
| 打开设置；进入系统设置；查找设置模块 | [设置首页](pages/home/README.md) | 启动设置 |
| 磨砂玻璃；清透水晶；界面透明效果；材质 | [界面材质](pages/interface_material/README.md) | 设置 > 显示和亮度 > 界面材质 |
| 切换输入法；管理屏幕键盘；实体键盘；鼠标速度 | [键盘、输入法与鼠标](pages/keyboard/README.md) | 设置 > 通用设置 > 键盘；鼠标入口按连接状态 |
| 切换系统语言；添加语言；语言排序；删除语言 | [语言](pages/language/README.md) | 设置 > 通用设置 > 语言 |
| 开源许可；隐私政策；进网许可；监管信息 | [法律与监管信息](pages/legal/README.md) | 设置 > 关于平板电脑 > 法律信息／监管信息 |
| GPS；定位开关；位置权限；最近使用位置 | [位置信息](pages/location/README.md) | 设置 > 位置信息 |
| 免打扰；勿扰；睡眠模式；允许打扰 | [模式与勿扰](pages/modes/README.md) | 设置 > 声音和振动 > 模式 > 勿扰／睡眠 |
| 添加用户；访客模式；切换用户；修改头像 | [多用户](pages/multi_user/README.md) | ROW：设置 > 通用设置 > 多用户 |
| 锁屏通知；通知历史；角标；电量百分比；实时网速；控制中心样式 | [通知和控制中心](pages/notifications/README.md) | 设置 > 通知和控制中心 |
| 注视不息屏；靠近亮屏；距离提醒；护眼距离 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) | 高级功能 > 实验室；PRC 距离提醒在学习助手 > 健康护眼 |
| 隐私看板；剪贴板提示；锁屏隐藏敏感信息；用户体验计划 | [隐私保护／隐私控制](pages/privacy/README.md) | PRC：设置 > 隐私保护；ROW：安全和隐私内相关入口 |
| 阅读黑白；电子书显示；墨纸；彩纸；阅读省电 | [阅读模式](pages/reading_mode/README.md) | 设置 > 显示和亮度 > 阅读模式 |
| 高刷；调刷新率；限制帧率；设置120Hz；高刷新率应用 | [屏幕刷新率](pages/refresh_rate/README.md) | 设置 > 显示和亮度 > 屏幕刷新率 |
| 恢复出厂；重置网络；重置应用偏好；清除所有数据 | [重置选项](pages/reset/README.md) | 设置 > 通用设置 > 重置选项 |
| 改提示音；通知铃声；自定义铃声；用录音作铃声 | [铃声选择](pages/ringtones/README.md) | 设置 > 声音和振动 > 通知铃声／其他铃声入口 |
| 安装未知应用；安全中心；紧急联系人；SOS；医疗信息 | [安全、隐私与紧急情况](pages/safety/README.md) | PRC：设置 > 安全；ROW：安全和隐私／安全和紧急情况 |
| 自动开机；自动关机；定时重复；设置工作日关机 | [定时开关机](pages/scheduled_power/README.md) | 设置 > 通用设置 > 定时开关机 |
| 屏幕偏黄；调色温；冷暖色；色彩模式 | [屏幕色调](pages/screen_color/README.md) | 设置 > 显示和亮度 > 屏幕色调 |
| 自动锁屏时间；休眠时间；自动息屏；屏幕超时；保持屏幕亮 | [屏幕熄灭时间](pages/screen_timeout/README.md) | 设置 > 显示和亮度 > 屏幕熄灭时间 |
| 搜索设置项；按关键词找功能；搜索历史 | [设置搜索](pages/search/README.md) | 设置首页 > 搜索框 |
| 媒体音量；闹钟音量；静音；静音时关闭媒体；充电提示音 | [声音和振动](pages/sound/README.md) | 设置 > 声音和振动（无振动硬件时为声音） |
| 查MAC地址；序列号；IMEI；EID；复制EID | [状态信息](pages/status/README.md) | 设置 > 关于平板电脑 > 状态信息 |
| 空间不足；查看容量；清理空间；SD卡格式化；卸载SD卡 | [存储](pages/storage/README.md) | 设置 > 通用设置 > 存储 |
| 查看手写笔连接；外接键盘状态；笔配对 | [手写笔和键盘](pages/stylus_keyboard/README.md) | 设置 > 手写笔和键盘 |
| 来电震动；通知震动；触感反馈；先震动后响铃 | [振动设置](pages/vibration/README.md) | 设置 > 声音和振动 > 振动和触感反馈 |
| 左右双栏；滚动错区域；分屏后找不到按钮 | [设置自适应布局](features/adaptive_layout/README.md) | 设置各页面 |
| 磁贴和设置同步；静音联动；振动联动；锁屏通知同步 | [控制中心及跨页状态同步](features/control_center_sync/README.md) | 控制中心与设置对应入口 |
| 桌面深色开关；移除深浅色组件 | [深浅模式桌面小组件](features/dark_widget/README.md) | 桌面 > 深浅模式小组件 |
| 移除首页推荐；设置建议卡片；关闭建议 | [首页设置建议](features/suggestions/README.md) | 设置首页 > 建议卡片 |
| 展开音量面板；调单个应用音量；通话音量；物理音量键 | [物理音量键与音量面板](features/volume_panel/README.md) | 按设备音量键 |

## 具体操作 → 目标页面

以下操作名称摘自页面事实，便于按动词检索；具体做法和结果只在页面正文维护。包含排查类条目时，它们是诊断线索，不自动追加到测试用例。

| 具体操作／定位问题 | 读取页面 |
|---|---|
| 查看设备或系统参数 | [关于平板电脑](pages/about/README.md) |
| 查网络地址或序列号 | [关于平板电脑](pages/about/README.md) |
| 查许可证或监管资料 | [关于平板电脑](pages/about/README.md) |
| 进入账号操作 | [账号和服务／账号和同步](pages/accounts/README.md) |
| 查同步设置 | [账号和服务／账号和同步](pages/accounts/README.md) |
| 查找设备 | [账号和服务／账号和同步](pages/accounts/README.md) |
| 配置观影免打扰 | [高级功能与实验室](pages/advanced/README.md) |
| 配置智能收音 | [高级功能与实验室](pages/advanced/README.md) |
| 选择需要屏蔽通知的应用 | [高级功能与实验室](pages/advanced/README.md) |
| 总开关关闭后找不到应用列表 | [高级功能与实验室](pages/advanced/README.md) |
| 进入 AI 功能 | [AI 智慧服务](pages/ai_services/README.md) |
| 恢复想帮帮图标 | [AI 智慧服务](pages/ai_services/README.md) |
| 启动想帮帮 | [AI 智慧服务](pages/ai_services/README.md) |
| 创建分身 | [应用分身](pages/app_clone/README.md) |
| 删除分身 | [应用分身](pages/app_clone/README.md) |
| 创建按钮不可点 | [应用分身](pages/app_clone/README.md) |
| 确定正在操作正确应用 | [应用信息](pages/app_info/README.md) |
| 进入应用子设置 | [应用信息](pages/app_info/README.md) |
| 卸载或强停 | [应用信息](pages/app_info/README.md) |
| 分享应用（PRC） | [应用信息](pages/app_info/README.md) |
| 找到目标应用 | [应用管理](pages/app_management/README.md) |
| 调整列表顺序 | [应用管理](pages/app_management/README.md) |
| 查系统应用 | [应用管理](pages/app_management/README.md) |
| 重置应用偏好 | [应用管理](pages/app_management/README.md) |
| 播放背景音 | [背景音（仅入口存在时）](pages/background_sound/README.md) |
| 处理来电中断 | [背景音（仅入口存在时）](pages/background_sound/README.md) |
| 切换系统用户 | [背景音（仅入口存在时）](pages/background_sound/README.md) |
| 进入备份服务 | [备份](pages/backup/README.md) |
| 检查备份状态 | [备份](pages/backup/README.md) |
| 按时间切换外观 | [深浅色自动切换](pages/dark_mode/README.md) |
| 按日落日出切换 | [深浅色自动切换](pages/dark_mode/README.md) |
| 停止自动切换 | [深浅色自动切换](pages/dark_mode/README.md) |
| 手动修改日期或时间 | [日期和时间](pages/date_time/README.md) |
| 手动设置时区 | [日期和时间](pages/date_time/README.md) |
| 使用位置时区（ROW） | [日期和时间](pages/date_time/README.md) |
| 切换时间格式 | [日期和时间](pages/date_time/README.md) |
| 改变默认应用 | [默认应用](pages/default_apps/README.md) |
| 确认使用第三方 | [默认应用](pages/default_apps/README.md) |
| 保留系统默认 | [默认应用](pages/default_apps/README.md) |
| 改变外观 | [显示和亮度](pages/display/README.md) |
| 设置亮度 | [显示和亮度](pages/display/README.md) |
| 进入显示子功能 | [显示和亮度](pages/display/README.md) |
| 调整更多显示项 | [显示和亮度](pages/display/README.md) |
| 调整文字／显示大小 | [显示大小和文字](pages/display_size_text/README.md) |
| 切换粗体 | [显示大小和文字](pages/display_size_text/README.md) |
| 恢复设置 | [显示大小和文字](pages/display_size_text/README.md) |
| 切换音效模式 | [杜比音效](pages/dolby/README.md) |
| 调整音乐效果 | [杜比音效](pages/dolby/README.md) |
| 开关无法操作 | [杜比音效](pages/dolby/README.md) |
| 调整电影模式滑块 | [杜比音效](pages/dolby/README.md) |
| 调整护眼强度 | [护眼模式](pages/eye_comfort/README.md) |
| 配置时间计划 | [护眼模式](pages/eye_comfort/README.md) |
| 立即启用护眼 | [护眼模式](pages/eye_comfort/README.md) |
| 进入通用子功能 | [通用设置](pages/general/README.md) |
| 调整内存扩展（PRC） | [通用设置](pages/general/README.md) |
| 使用皮套模式 | [通用设置](pages/general/README.md) |
| 进入功能模块 | [设置首页](pages/home/README.md) |
| 首屏找不到入口 | [设置首页](pages/home/README.md) |
| 直接查找功能 | [设置首页](pages/home/README.md) |
| 切换材质 | [界面材质](pages/interface_material/README.md) |
| 识别提示状态 | [界面材质](pages/interface_material/README.md) |
| 管理输入法 | [键盘、输入法与鼠标](pages/keyboard/README.md) |
| 切换当前输入法 | [键盘、输入法与鼠标](pages/keyboard/README.md) |
| 定位切换图标 | [键盘、输入法与鼠标](pages/keyboard/README.md) |
| 调鼠标速度 | [键盘、输入法与鼠标](pages/keyboard/README.md) |
| 直接改变系统语言 | [语言](pages/language/README.md) |
| 管理多语言列表 | [语言](pages/language/README.md) |
| 调整语言优先级 | [语言](pages/language/README.md) |
| 删除语言 | [语言](pages/language/README.md) |
| 查协议或许可 | [法律与监管信息](pages/legal/README.md) |
| 验证监管信息 | [法律与监管信息](pages/legal/README.md) |
| 启用或关闭定位 | [位置信息](pages/location/README.md) |
| 查看哪些应用访问位置 | [位置信息](pages/location/README.md) |
| 配置应用位置权限 | [位置信息](pages/location/README.md) |
| 查找勿扰设置 | [模式与勿扰](pages/modes/README.md) |
| 检查通知是否应被抑制 | [模式与勿扰](pages/modes/README.md) |
| 添加用户 | [多用户](pages/multi_user/README.md) |
| 只创建、不切换 | [多用户](pages/multi_user/README.md) |
| 进入新用户或访客 | [多用户](pages/multi_user/README.md) |
| 编辑机主信息 | [多用户](pages/multi_user/README.md) |
| 修改锁屏通知 | [通知和控制中心](pages/notifications/README.md) |
| 调整状态栏信息 | [通知和控制中心](pages/notifications/README.md) |
| 调整锁屏下拉 | [通知和控制中心](pages/notifications/README.md) |
| 开启智能常亮 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) |
| 开启靠近唤醒 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) |
| 设定提醒距离 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) |
| 处理 KidsSpace 提醒 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) |
| 相关功能置灰 | [智能常亮、靠近亮屏与距离提醒](pages/presence/README.md) |
| 设置锁屏通知内容 | [隐私保护／隐私控制](pages/privacy/README.md) |
| 查看体验计划协议 | [隐私保护／隐私控制](pages/privacy/README.md) |
| 更改固定应用设置 | [隐私保护／隐私控制](pages/privacy/README.md) |
| 切换纸张效果 | [阅读模式](pages/reading_mode/README.md) |
| 开启智能阅读 | [阅读模式](pages/reading_mode/README.md) |
| 处理首次介绍 | [阅读模式](pages/reading_mode/README.md) |
| 按应用指定阅读效果 | [阅读模式](pages/reading_mode/README.md) |
| 使用阅读省电 | [阅读模式](pages/reading_mode/README.md) |
| 改变刷新率 | [屏幕刷新率](pages/refresh_rate/README.md) |
| 设置单个应用高刷 | [屏幕刷新率](pages/refresh_rate/README.md) |
| 查找列表中的应用 | [屏幕刷新率](pages/refresh_rate/README.md) |
| 启用全局手写笔 | [屏幕刷新率](pages/refresh_rate/README.md) |
| 重置网络 | [重置选项](pages/reset/README.md) |
| 重置应用偏好 | [重置选项](pages/reset/README.md) |
| 恢复出厂 | [重置选项](pages/reset/README.md) |
| 选择铃声 | [铃声选择](pages/ringtones/README.md) |
| 不使用通知铃声 | [铃声选择](pages/ringtones/README.md) |
| 使用本地音源 | [铃声选择](pages/ringtones/README.md) |
| 移除自定义条目 | [铃声选择](pages/ringtones/README.md) |
| 查找更多安全选项 | [安全、隐私与紧急情况](pages/safety/README.md) |
| 进入安全中心能力 | [安全、隐私与紧急情况](pages/safety/README.md) |
| 查找紧急资料设置 | [安全、隐私与紧急情况](pages/safety/README.md) |
| 设置开机或关机计划 | [定时开关机](pages/scheduled_power/README.md) |
| 选择预设重复 | [定时开关机](pages/scheduled_power/README.md) |
| 自定义星期 | [定时开关机](pages/scheduled_power/README.md) |
| 处理到时关机 | [定时开关机](pages/scheduled_power/README.md) |
| 切换色彩风格 | [屏幕色调](pages/screen_color/README.md) |
| 调整色温 | [屏幕色调](pages/screen_color/README.md) |
| 修改自动熄屏时长 | [屏幕熄灭时间](pages/screen_timeout/README.md) |
| 找不到永不等长时选项 | [屏幕熄灭时间](pages/screen_timeout/README.md) |
| 熄屏时间到但屏幕仍亮 | [屏幕熄灭时间](pages/screen_timeout/README.md) |
| 寻找设置项 | [设置搜索](pages/search/README.md) |
| 处理键盘遮挡 | [设置搜索](pages/search/README.md) |
| 结束搜索 | [设置搜索](pages/search/README.md) |
| 清理搜索记录 | [设置搜索](pages/search/README.md) |
| 调整指定声音 | [声音和振动](pages/sound/README.md) |
| 开启静音 | [声音和振动](pages/sound/README.md) |
| 静音时也关闭媒体 | [声音和振动](pages/sound/README.md) |
| 查找提示音选项 | [声音和振动](pages/sound/README.md) |
| 读取设备标识 | [状态信息](pages/status/README.md) |
| 查看 EID | [状态信息](pages/status/README.md) |
| 复制 EID | [状态信息](pages/status/README.md) |
| 查看或清理分类 | [存储](pages/storage/README.md) |
| 释放空间 | [存储](pages/storage/README.md) |
| 设置新 SD 卡 | [存储](pages/storage/README.md) |
| 格式化 SD 卡 | [存储](pages/storage/README.md) |
| 查看笔或键盘 | [手写笔和键盘](pages/stylus_keyboard/README.md) |
| 首页找不到键盘入口 | [手写笔和键盘](pages/stylus_keyboard/README.md) |
| 开启来电或通知振动 | [振动设置](pages/vibration/README.md) |
| 设置先振动再响铃 | [振动设置](pages/vibration/README.md) |
| 从控制中心关闭振动 | [振动设置](pages/vibration/README.md) |
| 操作前确认布局 | [设置自适应布局](features/adaptive_layout/README.md) |
| 找不见条目 | [设置自适应布局](features/adaptive_layout/README.md) |
| 旋转或调整窗口后继续 | [设置自适应布局](features/adaptive_layout/README.md) |
| 切换深浅色 | [控制中心及跨页状态同步](features/control_center_sync/README.md) |
| 切换静音 | [控制中心及跨页状态同步](features/control_center_sync/README.md) |
| 切换振动 | [控制中心及跨页状态同步](features/control_center_sync/README.md) |
| 改锁屏通知 | [控制中心及跨页状态同步](features/control_center_sync/README.md) |
| 配置智能收音 | [控制中心及跨页状态同步](features/control_center_sync/README.md) |
| 切换深浅模式 | [深浅模式桌面小组件](features/dark_widget/README.md) |
| 管理组件 | [深浅模式桌面小组件](features/dark_widget/README.md) |
| 查看体验计划建议 | [首页设置建议](features/suggestions/README.md) |
| 移除建议 | [首页设置建议](features/suggestions/README.md) |
| 进入建议的功能 | [首页设置建议](features/suggestions/README.md) |
| 调整音量 | [物理音量键与音量面板](features/volume_panel/README.md) |
| 显示其他通道 | [物理音量键与音量面板](features/volume_panel/README.md) |
| 关闭浮层 | [物理音量键与音量面板](features/volume_panel/README.md) |
| 调单个应用音量 | [物理音量键与音量面板](features/volume_panel/README.md) |

## 仅有入口信息的功能

| 功能 | 从哪里找 | 资料覆盖 |
|---|---|---|
| WLAN、移动网络、蓝牙、热点、NFC | [设置首页](pages/home/README.md)网络分组 | 未提供完整连接／认证流程 |
| 壁纸、个性化、灯效、息屏显示、锁屏 | [首页](pages/home/README.md)或[显示和亮度](pages/display/README.md) | 未提供完整子页 |
| 电池、游戏、无障碍、学习助手、一视界 | [首页](pages/home/README.md)对应模块 | 入口或部分联动条件 |
| 系统导航、任务栏、快捷手势、截屏录屏 | [通用设置](pages/general/README.md) | 入口定位 |
| 无界工作台、外设模式、视频通话助手 | [高级功能](pages/advanced/README.md) | 入口定位 |
| 安全中心、云服务、账号登录 | [安全](pages/safety/README.md)、[备份](pages/backup/README.md)、[账号](pages/accounts/README.md) | 跨 App 后需查目标资料 |

背景音等标有“仅入口存在时”的页面，只有当前界面确实出现对应功能才加载；缺失不应导致重复尝试。上述覆盖不足不等于产品无该功能。
