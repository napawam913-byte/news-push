# 数据源与命令行运行手册

本文档说明当前项目已经启用的数据源、暂未使用的数据源，以及如何在 Windows 命令行窗口里启动飞书推送。

当前项目只做三件事：

```text
真实数据源采集
规则筛选消息
推送到飞书机器人
```

当前项目不做：

```text
投资分析
个股推荐
估值判断
买卖建议
```

## 一、当前已用数据源

以下数据源已经接入代码，并且当前 `.env` 已开启。

| 数据源 | 采集器名称 | 当前用途 | 实时性理解 | 可信度理解 |
| --- | --- | --- | --- | --- |
| RSSHub 财经路由 | `rss` | 财联社、电报、东方财富关键词 RSS | 取决于 RSSHub 公共实例，可能延迟或超时 | 辅助源 |
| AKShare 财经快讯 | `akshare_realtime_news` | 财联社、东方财富、新浪、同花顺、富途、东方财富财经早餐 | 7x24 快讯，适合实时监控 | 主流财经平台 |
| AKShare 东方财富个股新闻 | `akshare_stock_news` | 按关注股票池抓东方财富个股新闻 | 较实时 | 主流财经平台 |
| 百度财经日历 | `baidu_calendar` | 宏观事件、财报披露、分红、停复牌 | 当天事件为主 | 日历/事件源 |
| 东方财富 A 股热度 | `stock_hot_rank` | 东方财富人气榜、飙升榜、百度 A 股热搜可用时采集 | 当前热度信号 | 市场热度源 |
| 央视新闻联播文字稿 | `cctv_news` | 宏观政策、产业政策类消息 | 通常不是分钟级实时 | 权威媒体/政策源 |
| 巨潮资讯公告 | `cninfo_announcements` | 按关注股票池抓上市公司公告 | 公告日有效 | 官方公告源 |
| 巨潮投资者关系 | `cninfo_relations` | 调研、投资者关系活动记录 | 通常按披露日有效 | 官方披露源 |
| 巨潮投资评级 | `cninfo_ratings` | 机构评级、评级变化 | 通常按发布日期有效 | 机构观点源 |
| 东方财富全市场公告 | `eastmoney_notices` | 全市场上市公司公告 | 公告日有效 | 公告聚合源 |
| 东方财富个股研报 | `eastmoney_research` | 按关注股票池抓研报 | 研报发布日期有效 | 机构观点源 |
| 财新数据通 | `caixin` | 财经新闻摘要，能识别 A 股时补股票代码 | 新闻源，非纯公告源 | 主流财经媒体 |

当前 `.env` 的启用状态：

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

当前关注股票池：

```text
STOCK_CODES=300750,002594,600519
CNINFO_STOCK_CODES=300750,002594,600519
EASTMONEY_RESEARCH_STOCK_CODES=300750,002594,600519
```

说明：

```text
STOCK_CODES
用于东方财富个股新闻。

CNINFO_STOCK_CODES
用于巨潮公告和巨潮投资者关系。

EASTMONEY_RESEARCH_STOCK_CODES
用于东方财富个股研报。
```

## 二、当前未用数据源

以下数据源暂未接入或未启用。

| 数据源 | 当前状态 | 未使用原因 |
| --- | --- | --- |
| 模拟数据源 | 已关闭 | 现在已切换为真实数据源，`ENABLE_SAMPLE_COLLECTOR=false` |
| Tushare Pro | 未接入 | 需要 token，部分高质量数据需要积分或权限 |
| Wind | 未接入 | 商业终端/商业授权 |
| Choice | 未接入 | 商业终端/商业授权 |
| 同花顺 iFinD | 未接入 | 商业终端/商业授权 |
| 交易所官网原始公告直连 | 未接入 | 需要单独适配上交所、深交所、北交所字段和反爬 |
| 自建 RSSHub | 未部署 | 当前先使用公共 RSSHub；自建后稳定性更好 |
| 付费新闻 API | 未接入 | 需要账号、密钥和费用 |
| 付费舆情 API | 未接入 | 需要账号、密钥和费用 |
| 飞书多维表格写入 | 代码已封装，当前未配置 | `.env` 里 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_BITABLE_APP_TOKEN`、`FEISHU_BITABLE_TABLE_ID` 为空 |
| 基本面评分 | 已关闭 | 当前需求只做消息投送和筛选，不做分析，`ENABLE_FUNDAMENTAL_SCORING=false` |

后续如果你要提高数据质量，优先级建议：

```text
1. 自建 RSSHub，提升 RSS 稳定性
2. 接入 Tushare Pro，补充更结构化的数据
3. 接入交易所官网原始公告，提升公告权威性
4. 再考虑 Wind / Choice / iFinD 等商业源
```

## 三、命令行窗口开启方式

### 方式一：只运行一次，用于测试

打开 Windows PowerShell，然后执行：

```powershell
cd D:\learning\news-push
.\.venv\Scripts\python.exe -m app.main --once
```

含义：

```text
--once
只跑一轮，跑完就退出。

适合测试：
是否能采集数据
是否能筛选消息
是否能推送飞书
```

### 方式二：一直运行，用于持续推送

打开 Windows PowerShell，然后执行：

```powershell
cd D:\learning\news-push
.\.venv\Scripts\python.exe -m app.main
```

这条命令没有 `--once`，所以会一直循环运行。

如果使用 exe：

```powershell
cd D:\learning\news-push\dist
.\news-push.exe
```

当前 `.env` 配置是：

```text
DRY_RUN=false
WORKDAY_ONLY=false
ACTIVE_START_HOUR=0
ACTIVE_END_HOUR=24
INTERVAL_MIN_SECONDS=300
INTERVAL_MAX_SECONDS=600
```

也就是：

```text
真实推送到飞书
全天运行
不限制工作日
每 5 到 10 分钟自动跑一轮
```

### 方式三：确认当前会加载哪些采集器

```powershell
cd D:\learning\news-push
.\.venv\Scripts\python.exe -B -c "from app.config import load_settings; from app.main import build_collectors; s=load_settings(); print([c.name for c in build_collectors(s)])"
```

正常应看到类似：

```text
['rss', 'akshare_realtime_news', 'akshare_stock_news', 'baidu_calendar', 'stock_hot_rank', 'cctv_news', 'cninfo_announcements', 'cninfo_relations', 'cninfo_ratings', 'eastmoney_notices', 'eastmoney_research', 'caixin']
```

如果使用 exe，更推荐：

```powershell
cd D:\learning\news-push\dist
.\news-push.exe --check-config
```

正常应看到：

```text
dry_run=False
webhook_configured=True
data_dir=D:\learning\news-push\data
```

## 四、窗口保持运行的注意事项

命令行窗口保持打开，程序就会持续运行。

如果你关闭 PowerShell 窗口，正常情况下程序会停止。

为避免异常关闭后残留后台进程，新版本已经加入单实例控制。持续运行时会写入：

```text
D:\learning\news-push\data\news-push.pid
```

查看是否仍在后台运行：

```powershell
cd D:\learning\news-push\dist
.\news-push.exe --status
```

如果看到：

```text
running=True
```

说明还有进程在后台运行。

停止后台运行：

```powershell
cd D:\learning\news-push\dist
.\news-push.exe --stop
```

正常会输出：

```text
stopped=True
```

再次查看：

```powershell
.\news-push.exe --status
```

应看到：

```text
running=False
```

如果已有一个持续运行进程，再次启动 `.\news-push.exe` 会直接退出并提示使用 `--status` 或 `--stop`，不会重复启动多个后台进程。

如果电脑睡眠、断网、关机，程序也会停止或无法正常采集。

停止程序：

```text
在 PowerShell 窗口按 Ctrl + C
```

或者使用：

```powershell
.\news-push.exe --stop
```

如果只是想放着运行：

```text
可以最小化窗口
不要关闭窗口
不要让电脑进入睡眠
```

## 五、如何判断推送是否真实和实时

飞书消息里重点看这几项：

```text
来源
发布时间
投送时间
原文链接
利好/利空/中性
一级/二级消息
```

判断原则：

```text
官方公告
看来源是否来自巨潮/交易所/公告聚合，重点看公告链接和公告日期。

财经快讯
看发布时间和投送时间差值，15 分钟内可以认为比较实时。

研报/评级
不按分钟级实时判断，按发布日期判断。

热榜/财经日历
是市场信号或事件日历，不等同于新闻事实本身。
```

公开数据源没有 100% SLA。当前系统的设计是：

```text
某个源失败，不影响其他源继续跑
所有消息本地去重
只把规则筛选后的一级/二级消息推送到飞书
未命中规则的消息只入库，不推送
```
