from __future__ import annotations

from app.models import NewsItem


class SampleCollector:
    name = "sample"

    def collect(self) -> list[NewsItem]:
        sample_publish_time = "2026-05-26 09:30:00"
        return [
            NewsItem(
                source="sample",
                source_type="announcement",
                publish_time=sample_publish_time,
                stock_code="300000",
                stock_name="示例股份",
                title="示例股份关于签订重大合同的公告",
                summary="公司签订重大项目合同，合同金额较大。",
                url="https://example.com/good-news-1",
                raw_content="公司签订重大项目合同，预计对未来经营业绩产生积极影响。",
            ),
            NewsItem(
                source="sample",
                source_type="announcement",
                publish_time=sample_publish_time,
                stock_code="600000",
                stock_name="测试银行",
                title="测试银行关于股东减持计划的公告",
                summary="股东拟减持公司股份。",
                url="https://example.com/bad-news-1",
                raw_content="股东因自身资金安排拟减持公司股份。",
            ),
        ]
