# A 股利好消息监控测试版

这是一个 A 股利好消息监控和飞书推送测试项目。

数据源清单、未启用数据源和命令行运行方式见：

```text
docs/runbook-data-sources.md
```

当前版本已经支持：

- 模拟数据采集
- AKShare 个股新闻采集
- RSS 数据源采集
- 巨潮资讯 CNINFO 公告采集
- 关键词利好/负面判断
- 本地去重
- 本地 JSONL 运行记录
- 飞书机器人推送
- 飞书批次热点摘要推送
- 工作日 7:00-24:00 调度窗口
- 2-3 小时随机推送间隔
- 规则筛选后的飞书消息投送
- 飞书多维表格写入封装
- dry-run 测试模式

默认不会上传真实密钥，`.env`、`.env.*`、`.venv` 和运行数据都已经被 `.gitignore` 忽略。

## 仓库地址

```text
https://github.com/napawam913-byte/news-push.git
```

## 目录结构

```text
news-push/
  app/
   collectors/
      cninfo_announcements.py
      akshare_stock_news.py
      rss.py
      sample.py
    feishu/
      client.py
    rules/
      classifier.py
    storage/
      local_store.py
    config.py
    main.py
    models.py
  config/
    rss_sources.example.txt
  data/
    .gitkeep
  docs/
    data-sources.md
  .env.example
  .env.akshare-test.example
  .env.rss-test.example
  requirements.txt
  run.ps1
```

## 在新电脑上继续开发

### 1. 安装基础环境

需要：

```text
Git
Python 3.11+
Windows PowerShell
```

当前本地测试使用的是 Python 3.13，也可以用 Python 3.11 或 3.12。

### 2. 克隆项目

```powershell
cd D:\learning
git clone https://github.com/napawam913-byte/news-push.git
cd news-push
```

如果没有 `D:\learning`，可以换成你自己的目录。

### 3. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. 创建本地配置

```powershell
Copy-Item .env.example .env
```

`.env` 是你的本地私密配置文件，不要提交到 GitHub。

测试阶段可以先保持：

```text
DRY_RUN=true
ENABLE_SAMPLE_COLLECTOR=true
ENABLE_RSS_COLLECTOR=false
ENABLE_AKSHARE_STOCK_NEWS=false
BATCH_PUSH_ENABLED=true
```

### 5. 跑通模拟数据

```powershell
.\.venv\Scripts\python.exe -m app.main --once
```

第一次运行应看到类似：

```text
collectors=sample dry_run=True
done new=2 pushed=1
```

现在默认是批次推送，控制台会打印一条类似 `【财经利好热点】` 的摘要消息，而不是每条利好单独推送。

第二次再运行通常会变成：

```text
done new=0 pushed=0
```

这是正常的，说明去重生效了。

如果想重新测试第一次效果：

```powershell
Remove-Item .\data\seen_ids.txt, .\data\messages.jsonl -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m app.main --once
```

## 配置真实飞书机器人

打开 `.env`，填写：

```text
DRY_RUN=false
FEISHU_WEBHOOK=你的飞书机器人 Webhook
```

然后清理去重记录并运行：

```powershell
Remove-Item .\data\seen_ids.txt, .\data\messages.jsonl -Force -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m app.main --once
```

如果成功，飞书群会收到：

```text
【A股利好监控】S级 - 重大合同
```

注意：真实 Webhook 属于密钥，不要写进 README、代码或提交记录。

## 测试 AKShare 数据源

AKShare 已写入 `requirements.txt`。安装依赖后，复制测试配置：

```powershell
Copy-Item .env.akshare-test.example .env.akshare-test
```

编辑 `.env.akshare-test`：

```text
STOCK_CODES=300750,002594,600519
```

然后运行：

```powershell
$env:ENV_FILE='.env.akshare-test'
.\.venv\Scripts\python.exe -m app.main --once
```

测试时建议保持：

```text
DRY_RUN=true
```

这样不会真的推送到飞书，只会在控制台打印。

## 配置巨潮资讯公告源

巨潮公告源通过 AKShare 的 `stock_zh_a_disclosure_report_cninfo` 接口获取。接口目标是巨潮资讯公告查询页，字段包含代码、简称、公告标题、公告时间、公告链接。

在 `.env` 中开启：

```text
ENABLE_CNINFO_COLLECTOR=true
CNINFO_STOCK_CODES=300750,002594,600519
CNINFO_MARKET=沪深京
CNINFO_CATEGORIES=
CNINFO_LOOKBACK_DAYS=7
```

说明：

```text
CNINFO_STOCK_CODES  要查询公告的股票池；为空时使用 STOCK_CODES
CNINFO_MARKET       默认沪深京
CNINFO_CATEGORIES   可留空表示全部公告；也可填业绩预告,风险提示,日常经营等
CNINFO_LOOKBACK_DAYS 每次查询最近多少天公告
```

AKShare 这个接口是按股票代码查询，不建议每 5-10 分钟扫全市场。更合适的方式是维护一个关注股票池，或者后续做“低频全市场公告扫描 + 高频关注池扫描”。

## 测试 RSS 数据源

复制 RSS 测试配置：

```powershell
Copy-Item .env.rss-test.example .env.rss-test
```

编辑 `.env.rss-test`：

```text
RSS_URLS=https://example.com/rss.xml
```

运行：

```powershell
$env:ENV_FILE='.env.rss-test'
.\.venv\Scripts\python.exe -m app.main --once
```

RSSHub 公开实例可能返回 403 或超时。正式使用时建议自建 RSSHub。

更多数据源说明见：

```text
docs/data-sources.md
```

## 飞书多维表格

当前已经封装了飞书多维表格写入客户端，但默认不启用。

如果要写入多维表格，需要在 `.env` 中配置：

```text
FEISHU_APP_ID=
FEISHU_APP_SECRET=
FEISHU_BITABLE_APP_TOKEN=
FEISHU_BITABLE_TABLE_ID=
```

这些也属于密钥，不要提交。

## 调度和推送节奏

连续运行时，默认只在工作日 7:00-24:00 执行：

```text
WORKDAY_ONLY=true
ACTIVE_START_HOUR=7
ACTIVE_END_HOUR=24
INTERVAL_MIN_SECONDS=7200
INTERVAL_MAX_SECONDS=10800
```

也就是每轮任务完成后，随机等待 2-3 小时再跑下一轮。`--once` 模式用于手动测试，会直接跑一次，不受时间窗限制。

## 消息筛选

项目只做消息筛选和飞书投送，不做投资分析、不做个股推荐。

```text
ENABLE_FUNDAMENTAL_SCORING=false
FUNDAMENTAL_REPORT_DATE=
MIN_FUNDAMENTAL_SCORE=70
QUALITY_STOCK_CODES=300750,002594,600519
MIN_RECOMMEND_SCORE=85
```

当前 `ENABLE_FUNDAMENTAL_SCORING=false`，不会读取财务指标，不会输出基本面分数或推荐分。

飞书推送只会包含已识别出 A 股代码的利好消息。RSS 里无法匹配到 A 股代码的行业新闻、未上市公司、港股/美股/ETF 等，只会进入本地记录，不会进入重点消息和个股推荐。

当前关注分三档：

```text
一级：强利好 / 强利空
  立即进入飞书报告。

二级：普通利好 / 普通利空 / 重要中性
  进入飞书汇总区，用于跟踪行业、政策、资金、风险变化。

三级：一般中性 / 噪音
  只入库，不推送。
```

市场/行业热点可以进入二级汇总，但不会被当成个股推荐。

如果真实 A 股新闻只写公司全称、品牌名、子公司名，可以维护别名表：

```text
config/stock_aliases.csv
```

格式：

```text
alias,stock_code,stock_name,note
中国国际金融股份有限公司,601995,中金公司,公司全称
蓝电品牌,601127,赛力斯,品牌
```

识别优先级是：别名表 > 6 位股票代码 > A 股简称。

## 常用开发命令

查看当前 Git 状态：

```powershell
git status
```

拉取最新代码：

```powershell
git pull
```

提交修改：

```powershell
git add .
git commit -m "Update project"
git push
```

运行一次任务：

```powershell
.\.venv\Scripts\python.exe -m app.main --once
```

持续运行：

```powershell
.\.venv\Scripts\python.exe -m app.main
```

## 本地生成文件

运行后会产生：

```text
data/messages.jsonl
data/seen_ids.txt
```

这些是本地运行记录和去重记录，不会提交到 GitHub。

## 当前限制

- 现在还是测试版，不是最终生产系统。
- 公开数据源没有 SLA。
- RSSHub 公共实例不稳定，建议后续自建。
- 利好判断目前主要靠规则，后续需要加入 LLM 二次分类。
- 当前只做规则筛选和消息投送，不做基本面分析、估值分析或推荐分。
- 飞书多维表格写入还需要真实字段配置后再联调。

## 下一步

建议开发顺序：

1. 完善 AKShare 股票池配置。
2. 接入巨潮资讯公告源。
3. 接入飞书多维表格真实写入。
4. 增加 LLM 二次分类。
5. 增加估值和行业比较：PE/PB 分位、行业 ROE 横向排名。
6. 接入连续多期趋势：最近 4-8 个季度稳定性。
7. 做服务器部署脚本。
8. 增加日志和错误告警。
