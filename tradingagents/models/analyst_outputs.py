"""
分析师输出的 Pydantic 模型

使用 LangChain 1.0 的结构化输出功能，确保类型安全和数据验证
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from datetime import date


class MarketAnalysis(BaseModel):
    """市场分析结果（技术分析）"""

    ticker: str = Field(description="股票代码，如 000001, 600519")
    company_name: str = Field(description="公司名称")
    analysis_date: str = Field(description="分析日期 (YYYY-MM-DD)")

    # 价格信息
    current_price: Optional[float] = Field(
        default=None,
        description="当前价格（元）"
    )
    price_change_pct: Optional[float] = Field(
        default=None,
        description="涨跌幅（%）"
    )

    # 技术分析
    trend: Literal["强势上涨", "温和上涨", "震荡", "温和下跌", "快速下跌"] = Field(
        description="整体趋势判断"
    )
    support_level: Optional[float] = Field(
        default=None,
        ge=0,
        description="支撑位（元）"
    )
    resistance_level: Optional[float] = Field(
        default=None,
        ge=0,
        description="压力位（元）"
    )

    # 技术指标
    ma5: Optional[float] = Field(default=None, description="5日均线")
    ma10: Optional[float] = Field(default=None, description="10日均线")
    ma20: Optional[float] = Field(default=None, description="20日均线")
    ma60: Optional[float] = Field(default=None, description="60日均线")

    macd_signal: Optional[Literal["金叉", "死叉", "中性"]] = Field(
        default=None,
        description="MACD信号"
    )
    rsi_value: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="RSI值 (0-100)"
    )
    rsi_signal: Optional[Literal["超买", "超卖", "中性"]] = Field(
        default=None,
        description="RSI信号"
    )

    # 成交量分析
    volume_signal: Optional[Literal["放量", "缩量", "正常"]] = Field(
        default=None,
        description="成交量信号"
    )

    # 投资建议
    recommendation: Literal["强烈买入", "买入", "持有", "卖出", "强烈卖出"] = Field(
        description="投资建议"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="置信度 (0-1)"
    )
    target_price: Optional[float] = Field(
        default=None,
        gt=0,
        description="目标价（元，可选）"
    )

    # 分析理由
    reasoning: str = Field(
        min_length=20,
        description="详细的分析理由，至少20个字符"
    )
    risk_factors: list[str] = Field(
        default_factory=list,
        description="主要风险因素列表"
    )

    # 关键观察点
    key_observations: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="关键技术观察点（最多5条）"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """验证置信度范围"""
        if not 0 <= v <= 1:
            raise ValueError("置信度必须在 0-1 之间")
        return v

    @field_validator("target_price")
    @classmethod
    def validate_target_price(cls, v: Optional[float], info) -> Optional[float]:
        """验证目标价合理性"""
        if v is not None and v <= 0:
            raise ValueError("目标价必须大于0")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "000001",
                "company_name": "平安银行",
                "analysis_date": "2025-11-15",
                "current_price": 12.50,
                "price_change_pct": 2.3,
                "trend": "温和上涨",
                "support_level": 12.00,
                "resistance_level": 13.20,
                "ma5": 12.30,
                "ma10": 12.10,
                "ma20": 11.95,
                "ma60": 11.50,
                "macd_signal": "金叉",
                "rsi_value": 58.5,
                "rsi_signal": "中性",
                "volume_signal": "放量",
                "recommendation": "买入",
                "confidence": 0.75,
                "target_price": 13.50,
                "reasoning": "技术面显示多头排列，MACD金叉，成交量放大，短期有望突破压力位",
                "risk_factors": ["大盘调整风险", "行业政策不确定性"],
                "key_observations": [
                    "均线多头排列",
                    "MACD金叉向上",
                    "成交量明显放大",
                    "RSI处于健康区间"
                ]
            }
        }


class NewsAnalysis(BaseModel):
    """新闻分析结果"""

    ticker: str = Field(description="股票代码")
    company_name: str = Field(description="公司名称")
    analysis_date: str = Field(description="分析日期")

    # 新闻摘要
    news_count: int = Field(ge=0, description="分析的新闻数量")
    sentiment: Literal["非常正面", "正面", "中性", "负面", "非常负面"] = Field(
        description="整体舆情情绪"
    )
    sentiment_score: float = Field(
        ge=-1.0,
        le=1.0,
        description="情绪得分 (-1到1，-1最负面，1最正面)"
    )

    # 关键新闻
    key_news_summary: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="关键新闻摘要（最多5条）"
    )

    # 主题分类
    news_topics: list[str] = Field(
        default_factory=list,
        description="新闻主题标签"
    )

    # 影响评估
    impact_assessment: Literal["重大利好", "利好", "中性", "利空", "重大利空"] = Field(
        description="对股价的影响评估"
    )

    # 投资建议
    recommendation: Literal["强烈买入", "买入", "持有", "卖出", "强烈卖出"] = Field(
        description="基于新闻的投资建议"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")

    reasoning: str = Field(min_length=20, description="分析理由")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "000001",
                "company_name": "平安银行",
                "analysis_date": "2025-11-15",
                "news_count": 8,
                "sentiment": "正面",
                "sentiment_score": 0.65,
                "key_news_summary": [
                    "平安银行Q3净利润同比增长15%",
                    "推出创新金融产品服务小微企业",
                    "获评最佳零售银行奖"
                ],
                "news_topics": ["业绩增长", "产品创新", "行业荣誉"],
                "impact_assessment": "利好",
                "recommendation": "买入",
                "confidence": 0.70,
                "reasoning": "近期正面新闻较多，业绩增长稳健，市场情绪积极",
                "risk_factors": ["行业监管政策变化"]
            }
        }


class FundamentalsAnalysis(BaseModel):
    """基本面分析结果"""

    ticker: str = Field(description="股票代码")
    company_name: str = Field(description="公司名称")
    analysis_date: str = Field(description="分析日期")

    # 财务指标
    pe_ratio: Optional[float] = Field(default=None, ge=0, description="市盈率 P/E")
    pb_ratio: Optional[float] = Field(default=None, ge=0, description="市净率 P/B")
    roe: Optional[float] = Field(default=None, description="净资产收益率 ROE (%)")
    revenue_growth: Optional[float] = Field(
        default=None,
        description="营收增长率 (%)"
    )
    profit_growth: Optional[float] = Field(
        default=None,
        description="净利润增长率 (%)"
    )

    # 估值评估
    valuation: Literal["严重低估", "低估", "合理", "高估", "严重高估"] = Field(
        description="估值水平"
    )

    # 财务健康度
    financial_health: Literal["优秀", "良好", "一般", "较差", "危险"] = Field(
        description="财务健康度"
    )

    # 成长性
    growth_potential: Literal["高成长", "稳健成长", "低成长", "负增长"] = Field(
        description="成长潜力"
    )

    # 投资建议
    recommendation: Literal["强烈买入", "买入", "持有", "卖出", "强烈卖出"] = Field(
        description="投资建议"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")

    reasoning: str = Field(min_length=20, description="分析理由")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素")

    # 关键财务亮点
    key_highlights: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="关键财务亮点"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "000001",
                "company_name": "平安银行",
                "analysis_date": "2025-11-15",
                "pe_ratio": 5.8,
                "pb_ratio": 0.72,
                "roe": 11.5,
                "revenue_growth": 8.3,
                "profit_growth": 15.2,
                "valuation": "低估",
                "financial_health": "良好",
                "growth_potential": "稳健成长",
                "recommendation": "买入",
                "confidence": 0.80,
                "reasoning": "估值处于历史低位，盈利能力稳健，成长性良好",
                "risk_factors": ["利率波动风险", "信贷质量风险"],
                "key_highlights": [
                    "PE仅5.8倍，低于行业平均",
                    "ROE保持双位数增长",
                    "净利润增速超过15%",
                    "资产质量持续改善"
                ]
            }
        }


class SocialMediaAnalysis(BaseModel):
    """社交媒体分析结果"""

    ticker: str = Field(description="股票代码")
    company_name: str = Field(description="公司名称")
    analysis_date: str = Field(description="分析日期")

    # 社交媒体指标
    discussion_volume: Literal["极高", "高", "中等", "低", "极低"] = Field(
        description="讨论热度"
    )
    sentiment: Literal["非常乐观", "乐观", "中性", "悲观", "非常悲观"] = Field(
        description="投资者情绪"
    )
    sentiment_trend: Literal["快速上升", "上升", "平稳", "下降", "快速下降"] = Field(
        description="情绪趋势"
    )

    # 关键话题
    hot_topics: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="热门话题"
    )

    # 影响力用户观点
    influencer_sentiment: Optional[Literal["看多", "中性", "看空"]] = Field(
        default=None,
        description="影响力用户的整体观点"
    )

    # 投资建议
    recommendation: Literal["强烈买入", "买入", "持有", "卖出", "强烈卖出"] = Field(
        description="基于社交媒体的投资建议"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")

    reasoning: str = Field(min_length=20, description="分析理由")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素")

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "000001",
                "company_name": "平安银行",
                "analysis_date": "2025-11-15",
                "discussion_volume": "高",
                "sentiment": "乐观",
                "sentiment_trend": "上升",
                "hot_topics": ["业绩超预期", "数字化转型", "零售银行"],
                "influencer_sentiment": "看多",
                "recommendation": "买入",
                "confidence": 0.65,
                "reasoning": "社交媒体讨论热度高，投资者情绪乐观，关注度持续提升",
                "risk_factors": ["散户情绪波动大", "可能存在过度乐观"]
            }
        }


class ChinaMarketAnalysis(BaseModel):
    """中国市场专项分析结果"""

    ticker: str = Field(description="股票代码")
    company_name: str = Field(description="公司名称")
    analysis_date: str = Field(description="分析日期")

    # 市场环境
    market_environment: Literal["牛市", "震荡市", "熊市"] = Field(
        description="市场大环境"
    )
    sector_performance: Literal["强于大盘", "与大盘同步", "弱于大盘"] = Field(
        description="所属行业表现"
    )

    # 政策影响
    policy_impact: Optional[Literal["重大利好", "利好", "中性", "利空", "重大利空"]] = Field(
        default=None,
        description="政策影响评估"
    )

    # 资金流向
    capital_flow: Optional[Literal["大幅流入", "流入", "平衡", "流出", "大幅流出"]] = Field(
        default=None,
        description="主力资金流向"
    )

    # 机构动向
    institutional_action: Optional[Literal["增持", "持有", "减持"]] = Field(
        default=None,
        description="机构投资者动向"
    )

    # 投资建议
    recommendation: Literal["强烈买入", "买入", "持有", "卖出", "强烈卖出"] = Field(
        description="投资建议"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="置信度")

    reasoning: str = Field(min_length=20, description="分析理由")
    risk_factors: list[str] = Field(default_factory=list, description="风险因素")

    # 中国特色指标
    key_china_factors: list[str] = Field(
        default_factory=list,
        description="关键中国市场因素"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "000001",
                "company_name": "平安银行",
                "analysis_date": "2025-11-15",
                "market_environment": "震荡市",
                "sector_performance": "强于大盘",
                "policy_impact": "利好",
                "capital_flow": "流入",
                "institutional_action": "增持",
                "recommendation": "买入",
                "confidence": 0.75,
                "reasoning": "金融支持实体经济政策利好，机构资金持续流入，行业景气度提升",
                "risk_factors": ["宏观经济不确定性", "房地产市场波动"],
                "key_china_factors": [
                    "政策支持金融创新",
                    "北向资金持续流入",
                    "QFII增持金融股"
                ]
            }
        }
