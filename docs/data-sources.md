# 数据源接入说明

## 第一阶段策略

测试版先接三类数据源：

```text
RSSHub 财经路由
AKShare 个股新闻
后续公告采集器
```

当前推荐先跑 RSSHub，因为它最容易验证完整流程。

## 1. RSSHub

RSSHub 官方财经路由里有财联社电报、东方财富搜索、每经网、财经网等路由。

参考：

```text
https://rsshub.netlify.app/routes/finance
```

本项目已提供预设：

```text
config/rss_sources.example.txt
```

启用方式：

```text
ENABLE_SAMPLE_COLLECTOR=false
ENABLE_RSS_COLLECTOR=true
RSS_URLS=https://rsshub.app/cls/telegraph/announcement,https://rsshub.app/eastmoney/search/%E4%B8%AD%E6%A0%87
```

建议测试时先保持：

```text
DRY_RUN=true
```

也可以复制专用测试配置，不影响真实 `.env`：

```powershell
Copy-Item .env.rss-test.example .env.rss-test
$env:ENV_FILE='.env.rss-test'
.\.venv\Scripts\python.exe -m app.main --once
```

确认不会误推送后，再改成：

```text
DRY_RUN=false
```

## 2. AKShare 个股新闻

AKShare 官方文档说明它提供 A 股股票数据，并包含东方财富指定个股新闻资讯接口。

参考：

```text
https://akshare.akfamily.xyz/data/stock/stock.html
```

安装：

```powershell
.\.venv\Scripts\python.exe -m pip install akshare
```

启用：

```text
ENABLE_SAMPLE_COLLECTOR=false
ENABLE_AKSHARE_STOCK_NEWS=true
STOCK_CODES=300750,002594,600519
```

适合：

```text
关注股票池
个股新闻监控
后续和飞书多维表格股票池联动
```

## 3. 公告源

公告源是正式版的重点，优先级：

```text
巨潮资讯
上交所公告
深交所公告
北交所公告
```

公告类消息权威性高，但采集器需要单独适配字段和反爬限制。建议等 RSSHub 和 AKShare 跑通后再接。

## 推荐上线顺序

```text
1. RSSHub 财联社/东方财富搜索
2. AKShare 个股新闻
3. 巨潮资讯公告
4. 交易所公告
5. 飞书多维表格规则配置
```

## 注意

公开源不提供 SLA，适合作为第一阶段和轻量生产验证。后续如果依赖度变高，应逐步增加商业授权数据源或至少保留双源校验。
