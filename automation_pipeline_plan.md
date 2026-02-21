# 核心自动化编剧与合成全链路 (Automation Pipeline) 开发计划

本文档详细规划了**全链路短视频无人值守生产线 (Node 2 - Node 5)** 的开发阶段、阶段产出物与具体实施计划。它将过去人工组装视频的经验（MVP）抽象为可被机器自动化调度的 Python 引擎。

---

## 🏗️ 核心系统架构架构 (Pipeline Architecture)

整个后台引擎以 `database_builder/pipeline/automation_engine.py` 为核心入口，按顺序串联以下子模块：

1. **LLM Node (Node 2)**: 读取数据库 -> 拼接 `System Prompt` -> 调用 Gemini 3 -> 提取八镜头 JSON 脚本 -> 写入数据库。
2. **Audio Node (Node 3A)**: 读取 JSON -> 提取 `audio_narration` -> 调用 Edge-TTS -> 生成并保存 `.wav` 文件。
3. **Vision Node (Node 3B)**: 读取 JSON -> 提取 `image_prompt` -> 调用 Flux API (或占位符逻辑) -> 并行生成 8 张 `.png` 图片。
4. **Render Node (Node 4)**: 执行系统命令调度前台 Remotion React 项目 -> 传入包含 JSON/路径的高级参数 -> 物理压制出 1080P `.mp4`。
5. **Data Node (Node 5)**: 更新 Web UI 状态 -> 触发发布动作纪录 (初期提供 API 空壳用于后续爬虫接管)。

---

## 📅 阶段实施计划 (Phases & Timelines)

### 阶段一：破局！打造大模型王牌编剧 (Node 2)
**目标:** 写出最核心的剧本生成器，保证 AI 吐出的 JSON 格式与我们的 React 物理渲染模板 100% 对应。
*   **开发任务:**
    1.  建立 `pipeline/node_script_gen.py`。
    2.  设计强力的 System Script Prompt (基于 Day 1 验证的人类提示词改造)。
    3.  利用 Pydantic 约束大模型的输出，强行要求吐出含 8 个 `scenes` 的 `Script Model`。
    4.  处理 API 返回并更新 `video_jobs` 表的 `script_json` 字段。
*   **阶段产出物:**
    *   `node_script_gen.py` 自动化脚本生成器模块。
    *   Web 页面里的 Node 2 状态变为绿灯，可以在 UI 上的多行文本框看到精准的 JSON 嵌套结果。

### 阶段二：音画资产并发生成器 (Node 3)
**目标:** 把剧本变成实打实的物理资产 (`.wav` 和 `.png` 文件) 存入本地硬盘。
*   **开发任务:**
    1.  建立 `pipeline/node_assets_gen.py`。
    2.  **音频生成:** 对接免费的 `edge-tts`，抓取 JSON 里面的口播内容生成高质量旁白。
    3.  **图像生成:** (可选真假打) 因为调用 Flux API 需要买 Token，在此开发阶段首先写一个**“占位符下载器”**模块保底（去随机下载对应数量的高清壁纸作为替身）。同时封装出真实 `replicate/flux-schnell` 的请求代码，供你后续填入 API Key 激活。
    4.  更新数据库记录这 9 个文件的绝对物理路径。
*   **阶段产出物:**
    *   `node_assets_gen.py` 资产合并中心。
    *   控制台 Node 3 亮起，硬盘对应事件 ID 的专属文件夹里出现了音频和图片。

### 阶段三：Remotion 跨子系统引擎通讯 (Node 4)
**目标:** 由 Python 爬虫系统主动踢醒前端 React 集群进行成片压制。
*   **开发任务:**
    1.  建立 `pipeline/node_render.py`。
    2.  编写跨进程的 Subprocess 命令。让 Python 通过 `npm run build` 命令行带参数传给 Remotion 编译器。
    3.  将 Python 数据库里的 JSON 剧本路径作为环境变量 (`process.env`) 注入到 React 的执行上下文中。
    4.  截获 FFmpeg 输出，更新数据库最终兵器成片地址。
*   **阶段产出物:**
    *   `node_render.py` 物理渲染发起器。
    *   控制台 Node 4 点亮，并可直接出现 `output/event_1847.mp4` 点击即可网页播放。

### 阶段四：全局调度器与 UI 联调 (Orchestrator integration)
**目标:** 把以上分散的螺丝钉组装成一台一键按下去就能从头跑到尾的 V8 引擎。
*   **开发任务:**
    1.  建立 `automation_orchestrator.py` 入口。
    2.  将 Web UI 上你点下的 **“下发生产”**、**“生成分镜”** 等按钮，真正链接到后端的这套 Python 代码。
    3.  (进阶可选) 编写轮询守护线程 (`cron` 或 `Celery`) 使得任务池里的 `PENDING` 任务能被自动认领并执行。
*   **阶段产出物:**
    *   后端 API `app.py` 彻底被激活，前后端交互闭环完成。
    *   完全可演示的自动化操作全流程。

---

## 🛠️ 下一步动作评估 (Action Items)

以上是完整的蓝图逻辑。只要完成这四大阶段，你每天在洗脸刷牙的时候只需要点一下手机网页的“生成”，系统就会替你去生成文案、跑资产并在电脑本地把片子压出来。

我们是否确认该开发计划无误？无误后，我将立即进入**[阶段一：破局！打造大模型王牌编剧 (Node 2)]** 的代码编写环节！
