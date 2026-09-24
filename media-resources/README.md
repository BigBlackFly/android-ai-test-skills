# 内置测试媒体

开会话后显式调用 `python tools/prepare --serial <serial> sdcard init`，清理设备用户文件并预置共 8 个文件、4,181,243 字节（约 4.2 MB）。调用时机与例外见 [执行前设备环境准备](../docs/执行前设备环境准备.md)。两张课程表图片推送到 `/sdcard/Pictures/`；其余素材按本地相对路径推送到 `/sdcard/media-resources/`。本说明文件不推送。

| 文件 | 格式/尺寸 | 说明 |
|---|---|---|
| [images/landscape_01.jpg](images/landscape_01.jpg) | JPG，700×437 | — |
| [images/landscape_02.jpg](images/landscape_02.jpg) | JPG，800×466 | — |
| [images/portrait_01.png](images/portrait_01.png) | PNG，291×349 | — |
| [images/portrait_02.png](images/portrait_02.png) | PNG，283×450 | — |
| [images/课程表1.png](images/课程表1.png) | PNG，403×390 | 目标：`/sdcard/Pictures/课程表1.png` |
| [images/课程表2.png](images/课程表2.png) | PNG，312×504 | 目标：`/sdcard/Pictures/课程表2.png` |
| [videos/sample_720p.mp4](videos/sample_720p.mp4) | MP4/H.264，1280×720 | 约 5 秒，无音轨 |
| [videos/sample_small.mp4](videos/sample_small.mp4) | MP4/H.264，176×144 | 5 秒，AAC 音轨 |

通用素材用于浏览、播放、编辑、删除和分享等测试；两张课程表图片供日历图库导入、课程表识别等用例使用，设备目标分别为 `/sdcard/Pictures/课程表1.png` 与 `/sdcard/Pictures/课程表2.png`。文件名供用例稳定引用，变更或删除时同步修改相关用例及 `tools/prepare/sdcard.py` 的目标映射。
