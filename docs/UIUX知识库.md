# 测试中使用 UIUX 知识

Agent 可以按需读取 `uiux/`目录下的 UIUX 设计知识，并查阅 `knowledge/`目录下的测试经验。Agent 应当围绕当前用例涉及的页面和交互逐步查询和加载。

## 入口与组织

UIUX 知识库的总入口为 [uiux/README.md](../uiux/README.md)。App 目录以 Android 包名组织；当前入口为[图库（com.zui.gallery）](../uiux/apps/com.zui.gallery/README.md)和[系统设置（com.zui.settings）](../uiux/apps/com.zui.settings/README.md)。

```text
uiux/
  README.md                    # App、包名和资料入口
  apps/<包名>/
    README.md                  # 页面与跨页主题索引
    functions.md               # 功能和检索词
    navigation.md              # 跨页导航
    limitations.md             # 适用版本和待确认事项
    sources.md                 # 来源和覆盖说明
    pages/<page_id>/README.md   # 页面规则，同级 images/ 放局部图
    features/<topic_id>/README.md
    sources/                   # 原始设计稿
```

## 阅读流程

1. 根据用例确认 App 和功能，通过总索引、App 索引及功能索引定位资料。跨 App 用例分别查找相关内容。
2. 读取当前页、目标页及必要中间页的正文与适用说明；跨页操作补读 navigation.md 和对应 features/。
3. 图标、布局或状态细节需要确认时，通过宿主图片工具打开相对路径指向的局部图，按需补充 overview 或来源原稿。
4. 结合用例要求、设计规则、操作经验和当前设备证据执行测试。资料缺失时采用已有依据继续。

例如验证图库删除与恢复，可先通过 functions.md 定位，再读取 recently_deleted 页面及操作起点页面。恢复落点和提示文案采用用例要求与当前设备证据核对。

## 执行中复查

对入口、交互或预期存在疑问，或上下文遗忘时，按包名、功能、页面和交互关键词重新查阅相关正文及配图。资料缺口和设计差异记入报告，验收标准沿用用户用例。

复查后仍有待确认的问题时，使用 `session.py pause --ask --reason "疑点"`，向用户说明已知事实和待确认事项；收到答复后恢复会话。

## 资料职责

- `uiux/` 保存设计预期，在测试期间保持只读。索引、正文、配图和来源由知识库维护者维护。
- `knowledge/` 保存实际测试中积累的操作经验；页面、锚点和去向维护在 `knowledge/paths/`，见 [知识卡与路径图](知识卡与路径图.md)。
- 测试断言使用当前设备证据，并以用户用例为验收依据。
- 设计资料中的版本标记、适用条件、占位图和待确认事项随正文保留。图像细节通过对应配图核对。
- 资料读取由 Agent 负责，在资料中遇到图片链接时，必须完整读取并理解图片内容。
