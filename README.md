# A股利好消息监控测试版

这是第一阶段测试版，用来验证完整流程：

```text
采集消息 -> 去重 -> 规则判断 -> 写入本地记录 -> 可选写入飞书多维表格 -> 可选推送飞书群
```

默认使用模拟数据，方便先本地跑通。后续可以逐步替换为 AKShare、RSSHub、巨潮资讯等真实数据源。

## 目录结构

```text
a-share-good-news-monitor-test/
  app/
    collectors/
    feishu/
    rules/
    storage/
    config.py
    main.py
  data/
    .gitkeep
  .env.example
  requirements.txt
  run.ps1
```

## 快速开始

在 Windows PowerShell 中执行：

```powershell
cd C:\Users\22164\Documents\之前\a-share-good-news-monitor-test
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m app.main --once
```

第一次运行会在 `data/messages.jsonl` 和 `data/seen_ids.txt` 中写入测试记录。

## 配置说明

复制 `.env.example` 为 `.env` 后修改。

测试阶段可以保持：

```text
DRY_RUN=true
ENABLE_SAMPLE_COLLECTOR=true
ENABLE_RSS_COLLECTOR=false
```

如果要推送飞书群：

```text
DRY_RUN=false
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

如果要写入飞书多维表格，需要配置：

```text
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_TABLE_ID=
```

## RSS 测试

如果你有 RSSHub 或其他 RSS 地址：

```text
ENABLE_RSS_COLLECTOR=true
RSS_URLS=https://example.com/rss.xml,https://example.com/another.xml
```

## 推送规则

默认：

```text
S/A 级消息会推送
B/C 级只入库
忽略级不推送
```

默认利好词和负面词在 `app/rules/classifier.py` 中。

## 下一步开发

1. 接入 AKShare 采集器。
2. 接入巨潮/交易所公告采集器。
3. 接入 LLM 二次分类。
4. 把本地 JSONL 替换或同步到飞书多维表格。
5. 部署到云服务器，用 systemd 常驻运行。
