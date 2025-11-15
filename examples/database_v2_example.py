"""
Database V2 使用示例
演示如何使用 TimescaleDB + Qdrant + Redis 新架构
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import List

# 导入数据库连接
from app.core.database_v2 import (
    init_database,
    close_database,
    get_database_health,
)

# 导入服务
from app.services.stock_service_v2 import (
    stock_info_service,
    market_quotes_service,
    financial_data_service,
)
from app.services.vector_store_service import (
    vector_store_service,
    news_vector_service,
)


async def example_1_stock_info():
    """示例1: 股票基础信息操作"""
    print("\n" + "="*60)
    print("示例1: 股票基础信息操作")
    print("="*60)

    # 1. 插入股票信息
    stock_data = {
        "symbol": "000001.SZ",
        "code": "000001",
        "name": "平安银行",
        "name_en": "Ping An Bank",
        "full_symbol": "000001.SZ",
        "market": "CN",
        "exchange": "SZSE",
        "exchange_name": "深圳证券交易所",
        "board": "主板",
        "industry": "银行",
        "industry_code": "J66",
        "sector": "金融",
        "area": "深圳",
        "currency": "CNY",
        "timezone": "Asia/Shanghai",
        "list_date": date(1991, 4, 3),
        "status": "L",
        "total_shares": 1943867.44,  # 万股
        "float_shares": 1943867.44,
        "is_hs": True,
        "data_source": "tushare",
        "data_version": 1,
    }

    success = await stock_info_service.upsert_stock_info(stock_data)
    print(f"✅ 插入股票信息: {'成功' if success else '失败'}")

    # 2. 查询股票信息
    info = await stock_info_service.get_stock_info("000001.SZ")
    if info:
        print(f"\n📊 股票信息:")
        print(f"  代码: {info['code']}")
        print(f"  名称: {info['name']}")
        print(f"  行业: {info['industry']}")
        print(f"  上市日期: {info['list_date']}")

    # 3. 搜索股票
    results = await stock_info_service.search_stocks(
        keyword="平安",
        market="CN",
        limit=5
    )
    print(f"\n🔍 搜索结果: 找到 {len(results)} 只股票")
    for stock in results:
        print(f"  - {stock['code']} {stock['name']}")


async def example_2_market_quotes():
    """示例2: 市场行情操作"""
    print("\n" + "="*60)
    print("示例2: 市场行情操作")
    print("="*60)

    # 1. 插入K线数据
    quote_data = {
        "time": datetime(2024, 1, 15, 15, 0, 0),
        "symbol": "000001.SZ",
        "open": 12.50,
        "high": 12.80,
        "low": 12.30,
        "close": 12.65,
        "pre_close": 12.45,
        "volume": 125000000,
        "amount": 1580000000,
        "change": 0.20,
        "pct_chg": 1.61,
        "turnover_rate": 6.43,
        "volume_ratio": 1.15,
        "pe": 5.20,
        "pe_ttm": 5.18,
        "pb": 0.82,
        "pb_mrq": 0.82,
        "total_mv": 2456.78,  # 亿元
        "circ_mv": 2456.78,
        "adj_factor": 1.0,
        "data_source": "tushare",
        "period": "daily",
    }

    success = await market_quotes_service.upsert_daily_quote(quote_data)
    print(f"✅ 插入K线数据: {'成功' if success else '失败'}")

    # 2. 查询最新行情
    latest = await market_quotes_service.get_latest_quote("000001.SZ")
    if latest:
        print(f"\n📈 最新行情:")
        print(f"  日期: {latest['time']}")
        print(f"  收盘: {latest['close']}")
        print(f"  涨跌幅: {latest['pct_chg']}%")
        print(f"  成交额: {latest['amount']/100000000:.2f}亿")

    # 3. 查询历史K线
    quotes = await market_quotes_service.get_daily_quotes(
        symbol="000001.SZ",
        start_date=date.today() - timedelta(days=30),
        limit=10
    )
    print(f"\n📊 最近10个交易日:")
    for q in quotes:
        print(f"  {q['time'].date()}: {q['close']} ({q['pct_chg']:+.2f}%)")

    # 4. 计算移动平均线
    ma_data = await market_quotes_service.get_moving_averages(
        symbol="000001.SZ",
        days=30
    )
    if ma_data:
        latest_ma = ma_data[0]
        print(f"\n📉 移动平均线:")
        print(f"  MA5:  {latest_ma.get('ma_5', 0):.2f}")
        print(f"  MA10: {latest_ma.get('ma_10', 0):.2f}")
        print(f"  MA20: {latest_ma.get('ma_20', 0):.2f}")
        print(f"  MA60: {latest_ma.get('ma_60', 0):.2f}")


async def example_3_financial_data():
    """示例3: 财务数据操作"""
    print("\n" + "="*60)
    print("示例3: 财务数据操作")
    print("="*60)

    # 1. 插入财务数据
    financial_data = {
        "time": datetime(2023, 12, 31),
        "symbol": "000001.SZ",
        "report_period": "20231231",
        "report_type": "annual",
        "ann_date": date(2024, 3, 15),
        # 资产负债表
        "total_assets": 489523.45,  # 百万元
        "total_liab": 452341.23,
        "total_equity": 37182.22,
        "cash_and_equivalents": 15234.56,
        # 利润表
        "total_revenue": 145678.90,
        "net_income": 35678.45,
        "net_income_attr_p": 35123.78,
        "basic_eps": 1.81,
        "diluted_eps": 1.81,
        # 现金流量表
        "n_cashflow_act": 12345.67,
        "n_cashflow_inv_act": -5678.90,
        "n_cashflow_fin_act": 3456.78,
        # 财务指标
        "roe": 15.67,
        "roa": 1.23,
        "gross_margin": 45.32,
        "net_margin": 24.47,
        "netprofit_margin": 24.47,
        "debt_to_assets": 92.41,
        "current_ratio": 1.15,
        "quick_ratio": 0.98,
        "bvps": 19.12,
        "data_source": "tushare",
    }

    success = await financial_data_service.upsert_financial_data(financial_data)
    print(f"✅ 插入财务数据: {'成功' if success else '失败'}")

    # 2. 查询最新财务数据
    latest = await financial_data_service.get_latest_financial("000001.SZ")
    if latest:
        print(f"\n💰 最新财务数据 ({latest['report_period']}):")
        print(f"  营业收入: {latest.get('total_revenue', 0):.2f} 百万元")
        print(f"  净利润: {latest.get('net_income', 0):.2f} 百万元")
        print(f"  ROE: {latest.get('roe', 0):.2f}%")
        print(f"  每股收益: {latest.get('basic_eps', 0):.2f} 元")

    # 3. 查询财务历史
    history = await financial_data_service.get_financial_history(
        symbol="000001.SZ",
        report_type="annual",
        limit=5
    )
    print(f"\n📊 最近5年年报:")
    for f in history:
        print(f"  {f['report_period']}: 净利润 {f.get('net_income', 0):.2f}M, ROE {f.get('roe', 0):.2f}%")


async def example_4_vector_search():
    """示例4: 向量搜索操作"""
    print("\n" + "="*60)
    print("示例4: 向量搜索操作 (Qdrant)")
    print("="*60)

    # 1. 初始化向量集合
    await vector_store_service.init_collections()
    print("✅ 向量集合初始化完成")

    # 2. 添加新闻向量（示例）
    # 注意: 实际应用中需要使用 OpenAI embedding API 生成真实向量
    fake_embedding = [0.1] * 1536  # 1536维零向量（仅示例）

    success = await news_vector_service.add_news(
        news_id="news_001",
        title="平安银行发布2023年年报：净利润同比增长15%",
        content="平安银行今日发布2023年年度报告，全年实现净利润356.78亿元，同比增长15.67%...",
        embedding=fake_embedding,
        metadata={
            "date": "2024-03-15",
            "source": "证券时报",
            "symbols": ["000001.SZ"],
            "industry": "银行",
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "category": "company_announcement",
            "url": "https://example.com/news/001"
        }
    )
    print(f"✅ 添加新闻向量: {'成功' if success else '失败'}")

    # 3. 搜索相关新闻
    results = await news_vector_service.search_news(
        query_vector=fake_embedding,
        symbols=["000001.SZ"],
        industry="银行",
        limit=5
    )
    print(f"\n🔍 搜索结果: 找到 {len(results)} 条相关新闻")
    for news in results:
        print(f"  - [{news['date']}] {news['title']}")
        print(f"    相似度: {news['score']:.4f}, 情绪: {news.get('sentiment')}")


async def example_5_health_check():
    """示例5: 数据库健康检查"""
    print("\n" + "="*60)
    print("示例5: 数据库健康检查")
    print("="*60)

    health = await get_database_health()

    print("\n💊 数据库健康状态:")
    for db_name, status in health.items():
        icon = "✅" if status["status"] == "healthy" else "❌"
        print(f"  {icon} {db_name}: {status['status']}")
        if status.get("details"):
            for key, value in status["details"].items():
                print(f"      {key}: {value}")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 Database V2 使用示例")
    print("="*60)

    try:
        # 初始化数据库连接
        print("\n正在初始化数据库连接...")
        await init_database()
        print("✅ 数据库连接初始化成功\n")

        # 运行所有示例
        await example_1_stock_info()
        await example_2_market_quotes()
        await example_3_financial_data()
        await example_4_vector_search()
        await example_5_health_check()

        print("\n" + "="*60)
        print("✅ 所有示例执行完成！")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 关闭数据库连接
        print("\n正在关闭数据库连接...")
        await close_database()
        print("✅ 数据库连接已关闭\n")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
