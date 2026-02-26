# 播客管线生成物料使用指南 (赵老哥：双人播客版)

本次生成的物料是《赵老哥：八年一万倍的股市传奇》的**双人播客版本**（一男一女对谈风格，类似"老高与小茉"）。
所有物料已就位，可直接用于直播间推流或播客平台分发。

## 1. 双人播客音轨 (Audio)

*   **完整播客 MP3**
    *   **路径**: `C:\work\code\todayInHistory\podcast_engine\podcast_final.mp3`
    *   **时长**: 约 7-8 分钟
    *   **大小**: 7.8 MB (192kbps, 32kHz)
    *   **角色配音**:
        *   男主播 (Host): `zhoukai` — 年轻、有节奏感的叙事型男声
        *   女嘉宾 (Guest): `zsy` — 甜美知性风女声，负责提问/惊讶/共情
    *   **用途**: 直接导入 OBS/直播姬推流，或上传至喜马拉雅、小宇宙等播客平台。

*   **结构化 JSON 剧本**
    *   **路径**: `C:\work\code\todayInHistory\podcast_engine\podcast_draft.json`
    *   **内容**: 49 条结构化对白（含 SSML 标签、语速/音调控制参数、3 个系统注入占位符）
    *   **用途**: 如需更换音色或微调语速，修改 JSON 后重新运行 `full_podcast_synth.py` 即可秒级重建。

## 2. 直播间原画 (Visual)

*   **竖屏直播间背景图**
    *   **路径**: `C:\work\code\todayInHistory\podcast_engine\podcast_room.png`
    *   **尺寸**: 竖屏 (适配 9:16 直播间)
    *   **内容**: 一男一女播客主播坐在现代感的录播室中，背景有霓虹灯光和股市数据全息投影
    *   **用途**: 作为直播间的静态底图，在 OBS 中叠加音频推流即可开播。

## 3. 快速使用方法

1. 打开 OBS 或任意推流软件
2. 添加图片源 → 选择 `podcast_room.png` 作为背景
3. 添加媒体源 → 选择 `podcast_final.mp3`
4. 开始推流 → 一个全自动的双人播客直播间即刻上线
