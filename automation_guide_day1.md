# 自动化流水线：Day 1 流程实现指南

为实现 `day1_script_xerox_alto.json` 中定义的工作流全自动化，未来我们将在 n8n 或类似工作流引擎中配置以下节点。

## 1. 自动化信息流时序图 (Mermaid)

```mermaid
sequenceDiagram
    participant Cron as n8n (Cron Trigger)
    participant DB as PostgreSQL (events_production)
    participant LLM as Claude 3.5 Sonnet / DeepSeek
    participant Output as Storage / JSON Parser
    
    Cron->>DB: 每天凌晨1点触发: SELECT * FROM ... WHERE date=Today LIMIT 1
    DB-->>Cron: 返回结构化历史事件 (标题, 背景, 详情)
    Cron->>LLM: 发送 System Prompt + 事件详情
    Note right of LLM: 核心系统级指令：<br>你是一个短视频百万大V编剧。<br>强制输出严格格式的 JSON Array。
    LLM-->>Cron: 生成的 JSON 格式剧本 (含 audio_script, scenes)
    Cron->>Output: 校验 JSON 格式并落盘存储 (dayN_script.json)
```

## 2. 核心大模型指令 (System Prompt) 设计

这是自动化稳定产出具有“网感”的 JSON 的核心资产。你需要在 n8n 的 HTTP Request 节点中配置如下 Prompt：

```text
【角色设定】
你是一个坐拥百万粉丝的科技科普区短视频大V。你的任务是根据传入的科技历史事件，写出一条极具吸引力的、时长一分钟左右（纯汉字250-280字左右）的短视频分镜脚本。

【内容要求】
1. 挖掘冷知识与冲突：不要平铺直叙，要突出“反认知”、“历史的巧合”或“名人趣事”。
2. 5秒原则：前两句必须是留存 Hook。
3. 结尾拔高：最后一句必须为全片上价值，引导点赞。

【结构化强制输出要求】
你必须且只能输出一个合法的 JSON，不要包裹在 Markdown 代码块里，字段如下：
- "event_date": 事件日期 (字符串)
- "event_title": 感性且有冲突的短标题 (字符串)
- "audio_script": 完整的口播稿全文 (总计约260字，不要换行符，中文字符不要加引号)
- "scenes": 对象数组，共 4-6 个分镜。每个对象包含：
  - "timestamp_start": 开始秒数 (整数)
  - "timestamp_end": 结束秒数 (整数)
  - "image_prompt": 用极高水准的英文书写的 Midjourney/Flux 提示词，描述画面核心元素、年代感氛围和摄影光效。
  - "animation": 运镜CSS名称（只能从 zoom_in_slow, zoom_out_slow, pan_left, pan_right 取值）
  - "caption": 对应的屏幕大字标题 (8-15个中文字)
```

## 3. 错误恢复机制 (Fallback)
在这个节点中，我们要预防 LLM 输出不合规的 JSON (例如漏掉括号)。
- 在 n8n 中挂载一个 `JSON Auto Fixer` 节点，或者在本地发起请求时设置 `response_format: {"type": "json_object"}` (如 OpenAI/Claude 支持)，强制大模型按对象结构返回，杜绝解析崩溃。
