# 自动化流水线：如何构建 5000+ 条历史数据库

为了回答“除了 Wikipedia 还能从哪找数据”以及“如何自动化生成上千条初始素材”，这里是详细的数据工程策略。

## 1. 突破维基百科：核心数据源矩阵
维基百科只是打底（约能提供 1000 条数据），另外 4000 条长尾且有趣的 IT 历史必须依靠以下**三大垂直领域 API/爬虫**：

### 1) 顶级开源项目发版库 (GitHub API)
**目标**：捕捉“改变世界的代码提交日”
- **方法**：调用 GitHub GraphQL API，查询全网 Star 数大于 50,000 的所有仓库（如 Linux内核, React, Vue, TensorFlow, Docker）。
- **提取指标**：按项目抓取它的 `created_at` (诞生之日) 和带有 `v1.0.0` tag 的 `published_at` (正式发布之日)。
- **效果**：“1991年8月25日，林纳斯·托瓦兹在新闻组宣布他正在写一个操作系统，Linux 诞生。”

### 2) 商业与投融资归档 (Hacker News / TechCrunch)
**目标**：捕捉“硅谷的商战与资本神话”
- **方法**：利用 Algolia 提供的 Hacker News Search API（完全免费，支持按时间戳过滤）。
- **提取指标**：写一个 Python 脚本，循环请求过去 15 年的每天的 Top 10 帖子，只筛选关键词包含 `Acquires`, `Launch`, `Shuts down`, `IPO` 的高赞新闻。
- **效果**：“2012年4月9日，仅有13名员工的 Instagram 被 Facebook 以10亿美元天价收购。”

### 3) 网络安全与漏洞编目 (CVE Database / Exploit-DB)
**目标**：捕捉“黑客与网络攻防史”。这是极其容易成为爆款的题材。
- **方法**：下载美国 NVD (National Vulnerability Database) 的开放 JSON 数据包。
- **提取指标**：筛选 CVSS 评分等于 10.0 (最高危级别) 且具有名字的著名漏洞（如 Heartbleed, WannaCry, Log4Shell）。
- **效果**：“2017年5月12日，WannaCry勒索病毒席卷全球，几十万台电脑被锁，无数公司停摆。”

---

## 2. “5000条冷启动” 的自动化爬取架构拆解

在实施方案的第一周之后，你需要用 1-2 周的心无旁骛，写一套轻量级的 Python 脚本引擎来灌库：

```python
# 核心架构伪代码 (Scrape -> LLM Parse -> DB)

import requests
import json
import psycopg2 # 连接 PostgreSQL

def fetch_raw_data():
    # 爬虫工厂函数：并发抓取 Wikipedia, Github, HackerNews 的非结构化 JSON/HTML
    return raw_data_list

def extract_with_llm(raw_text):
    # 【最核心的一步】：不要自己写正则表达式！
    # 直接把整块脏乎乎的 HTML、帖子正文丢给 DeepSeek API
    system_prompt = """
    你是一个IT历史学者。请从输入文本中提取核心的科技事件。
    必须严格输出如下格式的 JSON 数组：
    [{ "year": 2001, "month": 10, "day": 23, "title": "iPod 发布", "importance_score": 9 }]
    如果是闲聊、无关紧要的事件，直接跳过。
    """
    response = call_deepseek_api(prompt=system_prompt, text=raw_text, response_format="json_object")
    return response.json()['events']

def main():
    db_conn = psycopg2.connect("...")
    raw_data = fetch_raw_data()
    
    for item in raw_data:
        structured_events = extract_with_llm(item.text)
        
        for event in structured_events:
            if event['importance_score'] >= 5: # 只收录高价值事件
                # 写入 PostgreSQL (此处使用 UPSERT 语法去重)
                db_conn.execute("INSERT INTO events_production ... ON CONFLICT DO NOTHING")
                
# 一键运行，周末挂机两天，5000条高质量数据即可入库。
```

## 3. 回答关于 Day 2 素材获取的疑问
在 Day 2 MVP 阶段，你无需关注这 5000 条怎么来，请直接**跳过代码**。你昨天已经通过提示词从维基词条拿到了目标（Xerox Alto）。

关于你所提到的 **“不使用本地 TTS，使用云端服务”**：
完全正确，本地部署 TTS（如 ChatTTS 本地推断）需要极高的 GPU 算力且耗时极长。
在目前的商业化标准动作中，我们推荐直接接入如下云端 API：

1.  **首推中英双语：阿里云 DashScope (CosyVoice大模型 API)**。这是目前中文商业领域最自然的“播客/说书人”音色组合，支持 API 传入文本直接获取 `.mp3` 与精确的字级别时间戳数组，且有免费调用额度。
2.  **海外首选：ElevenLabs API**。如果是做出海账号，ElevenLabs 是毋庸置疑的统治者。
3.  **开发期替代方案**：通过调用 OpenAI 的 `tts-1` 模型 API（如 `alloy` 音色）。

---
在 Day 2，你需要：
1. 去 ElevenLabs 或 阿里云平台申请一个 API Key，或者使用其官方网页端。
2. 将 Day 1 的 JSON 中的 `audio_script` 贴进去，生成一段音频 `.mp3` 下载到 `assets/` 文件夹。
3. 同样使用云端 Midjourney / Flux API，依据 Prompt 生成图片并下载。
