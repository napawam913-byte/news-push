# A 股利好消息监控测试版

这是一个 A 股利好消息监控和飞书推送测试项目。

当前版本已经支持：

- 模拟数据采集
- AKShare 个股新闻采集
- RSS 数据源采集
- 关键词利好/负面判断
- 本地去重
- 本地 JSONL 运行记录
- 飞书机器人推送
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
- 飞书多维表格写入还需要真实字段配置后再联调。

## 下一步

建议开发顺序：

1. 完善 AKShare 股票池配置。
2. 接入巨潮资讯公告源。
3. 接入飞书多维表格真实写入。
4. 增加 LLM 二次分类。
5. 做服务器部署脚本。
6. 增加日志和错误告警。
