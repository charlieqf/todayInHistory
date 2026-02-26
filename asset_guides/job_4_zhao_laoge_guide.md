# 视频管线生成物料使用指南 (Job #4: 赵老哥篇)

本系统不仅能自动合成最终的 MP4 视频，更是一个**全自动的数字资产库**。
在每次生成视频的过程中，系统会吐出所有原始的高清媒体资产。这为您后续做小红书图文、B站视频二次剪辑、或者播客音频二次分发提供了极大的便利。

以下是本次《赵老哥：八年一万倍的股市传奇》的所有生成物料及本地绝对路径说明：

## 1. 核心文案与旁白音轨 (Audio)
这是整期节目的灵魂，如果您只需要做播客（Podcast），可以直接拿走这两项：

*   **纯文字终读本 (Text)**
    *   **路径**: `C:\work\code\todayInHistory\data\final_scripts_stocks\赵老哥_八年一万倍的股市传奇.txt`
    *   **用途**: 大约 5000 字的纯净解说词，已通过大模型过滤掉了所有特殊符号和转场提示词，非常适合用来发布公众号文章，或直接导入剪映当提词器。
*   **TTS 主讲人配音 (MP3)**
    *   **路径**: `C:\work\code\todayInHistory\video-generator\public\assets\job_4_narration.mp3`
    *   **用途**: 长达 16 分 41 秒的全篇顺畅人声，您可以直接拉进任何剪辑软件作为主音轨。
*   **悬疑底层背景乐 (BGM)**
    *   **路径**: `C:\work\code\todayInHistory\video-generator\public\assets\bgm\suspense_loop_1.mp3`
    *   **用途**: 如果您想另外配音，这里提供了频道的专属循环垫乐。

## 2. AI 电影级原画册 (Visuals)
系统根据文字的起伏，让 Gemini 自动指挥大语言绘画模型（Flux）生成了 18 张精美的高分辨率（1080×1920）竖屏原画。

*   **图片存放目录**: `C:\work\code\todayInHistory\video-generator\public\assets\`
*   **图片列表**:
    *   `job_4_scene_0.png` 到 `job_4_scene_17.png`
*   **用途指南**:
    *   **小红书利器**: 这 18 张图尺寸极其标准（9:16），您可以不用剪视频，直接把它们批量拖入小红书，配上文字底本，就是一篇极具爆款潜质的图文长贴。
    *   **视频转场素材**: 在您自己使用剪映混剪时，可随时调取这 18 个核心画面的高清原图做遮罩或特效。

## 3. 标准化成品视频 (Final Output)
这是由上述全部素菜通过 React Remotion 前端渲染引擎，直接缝合并带上了缓慢推拉特效（Ken Burns动画）的一体化成品。

*   **最终 MP4 视频路径**: `C:\work\code\todayInHistory\video-generator\out\job_4_final.mp4`
*   **参数**: 1080×1920 (竖屏 1080p), 30 fps, H.264 编码。
*   **用途**: 不需要任何修改，直接上传抖音、视频号、TikTok 等短视频和竖屏流媒体平台。所有字幕、音乐和特效已完成硬编码物理烧录。
