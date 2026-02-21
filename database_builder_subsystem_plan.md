# 🗄️ IT历史上的今天 - 自动化素材库 (Database Builder) 子系统规划

## 1. 核心目标
构建一个由 Python 驱动的离线流水线，在 **Windows 本地环境**中，自动从四大开源/资讯渠道抓取“科技史”相关的大事件生肉，并利用 LLM 进行信息提取与清洗，最终向本地 SQLite 数据库中写入 **首批 1000-5000 条** 结构化、高质量的视频候选素材。

本子系统是整个全自动视频频道的“弹药库”。

---

## 2. 数据流与管道设计 (Pipeline)

此系统将划分为 3 个核心阶段，以解耦和防范网络/API失败：

### 阶段一：Raw Data Scraper (生肉采集作业)
使用轻量级的 Python 并发网络请求去四大渠道抓取原始数据，并保存为原始文本/JSON格式。**不在此阶段做任何正则清洗。**
1.  **Wikipedia 爬虫 (`scrapers/wikipedia_scraper.py`)**：
    *   目标：提取 "Timeline of computing", "1990 in science" 等条目的结构化日历。
    *   特点：使用 `wikipedia-api` 或 `BeautifulSoup`，注意设置稳定的 User-Agent 防封IP。
2.  **GitHub API 爬虫 (`scrapers/github_scraper.py`)**：
    *   目标：调用 REST API 获取 Stars > 50,000 仓库的创立时间 (Created_at) 和第一个大版本发布时间。
    *   特点：极客情怀，天然结构化，但需要处理 GitHub API 的 Token Rate Limit。
3.  **Hacker News 爬虫 (`scrapers/hn_scraper.py`)**：
    *   目标：通过 Algolia API，按年份搜索 Points > 1000 的超级爆款新闻贴（如巨头收购、创始人离职）。
    *   特点：吃瓜八卦和商业战首选，文本多为新闻标题。
4.  **CVE Exploit-DB 提取 (`scrapers/cve_scraper.py`)**：
    *   目标：搜集 CVSS > 9.0，具有世界级影响力的黑客事件或重大漏洞爆发日。

### 阶段二：LLM Data Cleanser (大模型智脑清洗作业)
这是整个子系统中最性感的一环，彻底替代了传统的爬虫规则清洗。
*   脚本：`cleaner/llm_processor.py`
*   动作：读取上一阶段抓取的生肉，每次塞给大模型（如 ChatGPT Pro / OpenAI API，利用其超大上下文及顶级推理能力）几百行的文本。
*   **Prompt 强制约束**：
    > “你是一个 IT 历史档案员。从以下抓取文本中提取事实，过滤无意义噪音和非IT新闻。
    > 严格返回一个 JSON 数组，必须包含以下字段：
    > `month` (1-12), `day` (1-31), `year` (YYYY), `title` (30字内吸引人的标题), `summary` (对事件的简要描述), `category` (Hardware/Software/Company/Hacker/OpenSource), `importance_score` (1-10分，满分为改变世界格局，如断网或iPhone发布)”。
    > 如缺失确切月日，则直接丢弃不输出。”

### 阶段三：SQLite Storage & Enrichment (入库与沉淀)
*   **核心动作 (`db/storage.py`)**：将大模型返回的合格 JSON 数据，执行 `INSERT` 或根据 `(month, day, year, title)` 去重 `UPSERT` 存入本地的 `history_events.db` 文件。
*   **富文本扩写 (Enrichment)**：设定一个 Trigger，当数据成功写入且 `importance_score >= 8`（S级高优爆款）时，调用一次更贵、逻辑更强的模型（如 Claude 3.5 Sonnet），让其提前撰写一段 `rich_context`（包含事件发生的戏剧性背景、反转、深远影响），一并存入表内，作为未来渲染当天脚本的弹药库。

---

## 3. 技术栈预选 (Windows 开发期)

| 模块 | 推荐技术/库 | 说明 |
| :--- | :--- | :--- |
| **数据库** | `SQLite3` | 优先推荐。本地单文件即插即用，未来上云时迁移极简。 |
| **网络爬取** | `requests`, `BeautifulSoup4` | 针对简单的 Wikipedia 和 REST API。 |
| **自动化调度** | Python `asyncio` & `ThreadPoolExecutor` | 提纯阶段需高并发调用 LLM API，提高清洗速度。 |
| **智脑 LLM** | OpenAI API (ChatGPT Pro) | 作为目前最顶级的多模态和推理模型，极度擅长理解乱码般的 HTML 爬虫生肉并由于其庞大的知识库，能精准提纯和结构化。 |
| **质量兜底** | `pydantic` | 在写入 SQLite 之前，严格校验 LLM 返回的数据结构，防止弱智幻觉弄脏数据库。 |

## 4. 实施里程碑 (Milestones)

为了稳扎稳打，我们将采用瀑布流与敏捷结合的方式，分三个 Milestone 推进：

*   **Milestone 1：骨架与第一个爬虫**
    *   初始化 `database_builder` 目录和 SQLite schema 建表。
    *   写好 `wikipedia_scraper.py`，能成功把生肉抓取并临时存进 CSV 或 JSONL。
*   **Milestone 2：LLM 清洗管道通车**
    *   接通 OpenAI (ChatGPT) 的 API，完成一套极度稳定的 `Pydantic` 带参 Prompt。
    *   看着大模型把一条条错综复杂的维基页面变成了整齐的 JSON 打分数据，并成功写进 SQLite。
*   **Milestone 3：接通剩余水源 (HN & GitHub) & 扩写爆款**
    *   完善另外两个重要信息源的爬取。
    *   把 SQLite 的数据池填充到 1000 - 3000 条，并对高分事件完成深度 `rich_context` 文档撰写。

此规划文档将作为 Phase 2 的实施地图，确保素材搜集具有多样性、高价值以及系统级的健壮性。
