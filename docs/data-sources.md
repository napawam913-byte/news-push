# 数据源接入说明

当前项目优先接入 **免费、公开、无自有 API key** 的数据源。所有源只做消息采集、规则筛选和飞书投送，不做投资分析、不做个股推荐。

## 当前已接入并可开启的数据源

| 数据源 | 采集器 | 类型 | 说明 |
| --- | --- | --- | --- |
| RSSHub 财经路由 | `rss` | 财经新闻/RSS | 财联社、电报、东方财富搜索等 RSS 路由；公共实例不稳定，超时会跳过 |
| AKShare 财经快讯 | `akshare_realtime_news` | 7x24 快讯 | 财联社、东方财富、新浪、同花顺、富途、东方财富财经早餐 |
| AKShare 东方财富个股新闻 | `akshare_stock_news` | 个股新闻 | 按 `STOCK_CODES` 股票池抓东方财富个股新闻 |
| 百度财经日历 | `baidu_calendar` | 财经日历/财报/分红/停复牌 | 宏观事件、A 股财报披露、分红除权、停复牌提醒 |
| 东方财富 A 股热度 | `stock_hot_rank` | 热点榜 | 东方财富人气榜、飙升榜；百度 A 股热搜可用时自动采集 |
| 央视新闻联播文字稿 | `cctv_news` | 政策新闻 | 适合捕捉宏观政策和产业政策类中性消息 |
| 巨潮资讯公告 | `cninfo_announcements` | 个股公告 | 按关注股票池抓 CNINFO 公告 |
| 巨潮投资者关系 | `cninfo_relations` | 调研/投资者关系 | 按关注股票池抓调研和投资者关系记录 |
| 巨潮投资评级 | `cninfo_ratings` | 机构观点 | 抓巨潮评级预测中心的机构评级记录 |
| 东方财富全市场公告 | `eastmoney_notices` | 全市场公告 | 按日期抓全市场公告，数量大，依赖规则筛选 |
| 东方财富个股研报 | `eastmoney_research` | 个股研报 | 按股票池抓东方财富研报 |
| 财新数据通 | `caixin` | 财经新闻 | 财新数据通新闻摘要，能识别到 A 股时会补股票代码 |

## 当前 `.env` 推荐开启方式

```text
ENABLE_SAMPLE_COLLECTOR=false
ENABLE_RSS_COLLECTOR=true
ENABLE_AKSHARE_REALTIME_NEWS=true
ENABLE_AKSHARE_STOCK_NEWS=true
ENABLE_BAIDU_CALENDAR_COLLECTOR=true
ENABLE_STOCK_HOT_RANK_COLLECTOR=true
ENABLE_CCTV_NEWS_COLLECTOR=true
ENABLE_CNINFO_COLLECTOR=true
ENABLE_CNINFO_RELATION_COLLECTOR=true
ENABLE_CNINFO_RATING_COLLECTOR=true
ENABLE_EASTMONEY_NOTICE_COLLECTOR=true
ENABLE_EASTMONEY_RESEARCH_COLLECTOR=true
ENABLE_CAIXIN_COLLECTOR=true
```

关注股票池：

```text
STOCK_CODES=300750,002594,600519
CNINFO_STOCK_CODES=300750,002594,600519
EASTMONEY_RESEARCH_STOCK_CODES=300750,002594,600519
```

全市场公告和快讯类源数量很大，飞书报告只会展示规则筛选后的一级/二级消息，不会把所有入库消息都发出来。

## 关键参数

```text
AKSHARE_REALTIME_SOURCES=cls,eastmoney,sina,ths,futu,cjzc
AKSHARE_REALTIME_LIMIT_PER_SOURCE=50
BAIDU_CALENDAR_LOOKBACK_DAYS=1
BAIDU_ECONOMIC_MIN_IMPORTANCE=2
STOCK_HOT_RANK_TOP_N=20
CCTV_NEWS_LOOKBACK_DAYS=2
CNINFO_RATING_LOOKBACK_DAYS=3
EASTMONEY_NOTICE_LOOKBACK_DAYS=1
EASTMONEY_RESEARCH_LOOKBACK_DAYS=30
CNINFO_LOOKBACK_DAYS=7
CNINFO_RELATION_LOOKBACK_DAYS=30
```

## 数据源稳定性

AKShare 和 RSSHub 都是公开源，不保证 SLA。当前处理方式是：某个源超时或报错时打印 warning，然后继续跑其他源。

已知情况：

- RSSHub 公共实例经常 403 或超时，所以代码已把单个 RSS 请求超时缩短到 5 秒。
- 巨潮投资评级当天可能暂无数据，AKShare 会抛字段长度错误；采集器会跳过当天并继续查最近几天。
- 百度 A 股热搜接口偶发返回异常；东方财富人气榜和飙升榜作为主要热度源。

## 后续可选但需要额外条件的源

这些暂时没有默认接入，因为需要 token、商业授权或更复杂反爬维护：

```text
Tushare Pro
Wind / Choice / 同花顺 iFinD
交易所官网原始公告直连
自建 RSSHub
付费舆情/新闻 API
```
