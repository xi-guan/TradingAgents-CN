"""
股票数据服务 V2 - 基于 TimescaleDB
提供股票基础信息、行情数据、财务数据的统一访问接口
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import asyncpg

from app.core.database_v2 import get_pg_pool, execute_sql, execute_sql_one, execute_sql_value

logger = logging.getLogger(__name__)


# ============================================================================
# 股票基础信息服务
# ============================================================================

class StockInfoService:
    """股票基础信息服务"""

    @staticmethod
    async def get_stock_info(symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票基础信息

        Args:
            symbol: 标准化股票代码（如 000001.SZ）

        Returns:
            股票基础信息字典，如果不存在返回 None
        """
        try:
            query = """
                SELECT
                    symbol, code, name, name_en, full_symbol,
                    market, exchange, exchange_name, board,
                    industry, industry_code, sector,
                    area, currency, timezone,
                    list_date, delist_date, status,
                    total_shares, float_shares, lot_size,
                    is_hs, data_source, data_version,
                    created_at, updated_at
                FROM stock_info
                WHERE symbol = $1
            """

            row = await execute_sql_one(query, symbol)

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"获取股票信息失败 symbol={symbol}: {e}")
            return None

    @staticmethod
    async def search_stocks(
        keyword: Optional[str] = None,
        market: Optional[str] = None,
        industry: Optional[str] = None,
        status: str = 'L',
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        搜索股票

        Args:
            keyword: 搜索关键词（匹配代码或名称）
            market: 市场类型（CN/HK/US）
            industry: 行业
            status: 上市状态（L=上市, D=退市, P=暂停）
            limit: 返回数量
            offset: 偏移量

        Returns:
            股票列表
        """
        try:
            conditions = ["status = $1"]
            params = [status]
            param_count = 1

            if keyword:
                param_count += 1
                conditions.append(f"(code LIKE ${param_count} OR name LIKE ${param_count})")
                params.append(f"%{keyword}%")

            if market:
                param_count += 1
                conditions.append(f"market = ${param_count}")
                params.append(market)

            if industry:
                param_count += 1
                conditions.append(f"industry = ${param_count}")
                params.append(industry)

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT
                    symbol, code, name, full_symbol,
                    market, exchange, industry, area,
                    list_date, status, is_hs
                FROM stock_info
                WHERE {where_clause}
                ORDER BY symbol
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """

            params.extend([limit, offset])
            rows = await execute_sql(query, *params)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            return []

    @staticmethod
    async def upsert_stock_info(stock_data: Dict[str, Any]) -> bool:
        """
        插入或更新股票基础信息

        Args:
            stock_data: 股票数据字典

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            pool = get_pg_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO stock_info (
                        symbol, code, name, name_en, full_symbol,
                        market, exchange, exchange_name, board,
                        industry, industry_code, sector,
                        area, currency, timezone,
                        list_date, delist_date, status,
                        total_shares, float_shares, lot_size,
                        is_hs, data_source, data_version
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18,
                        $19, $20, $21, $22, $23, $24
                    )
                    ON CONFLICT (symbol) DO UPDATE SET
                        name = EXCLUDED.name,
                        name_en = EXCLUDED.name_en,
                        exchange_name = EXCLUDED.exchange_name,
                        board = EXCLUDED.board,
                        industry = EXCLUDED.industry,
                        industry_code = EXCLUDED.industry_code,
                        sector = EXCLUDED.sector,
                        total_shares = EXCLUDED.total_shares,
                        float_shares = EXCLUDED.float_shares,
                        status = EXCLUDED.status,
                        data_version = EXCLUDED.data_version,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    stock_data.get('symbol'),
                    stock_data.get('code'),
                    stock_data.get('name'),
                    stock_data.get('name_en'),
                    stock_data.get('full_symbol'),
                    stock_data.get('market'),
                    stock_data.get('exchange'),
                    stock_data.get('exchange_name'),
                    stock_data.get('board'),
                    stock_data.get('industry'),
                    stock_data.get('industry_code'),
                    stock_data.get('sector'),
                    stock_data.get('area'),
                    stock_data.get('currency', 'CNY'),
                    stock_data.get('timezone', 'Asia/Shanghai'),
                    stock_data.get('list_date'),
                    stock_data.get('delist_date'),
                    stock_data.get('status', 'L'),
                    stock_data.get('total_shares'),
                    stock_data.get('float_shares'),
                    stock_data.get('lot_size'),
                    stock_data.get('is_hs', False),
                    stock_data.get('data_source'),
                    stock_data.get('data_version', 1)
                )

            logger.info(f"✅ 股票信息已保存: {stock_data.get('symbol')}")
            return True

        except Exception as e:
            logger.error(f"保存股票信息失败: {e}")
            return False


# ============================================================================
# 行情数据服务
# ============================================================================

class MarketQuotesService:
    """市场行情服务"""

    @staticmethod
    async def get_latest_quote(symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新行情

        Args:
            symbol: 股票代码

        Returns:
            最新行情数据
        """
        try:
            query = """
                SELECT
                    time, symbol, open, high, low, close, pre_close,
                    volume, amount, change, pct_chg,
                    turnover_rate, volume_ratio,
                    pe, pe_ttm, pb, pb_mrq,
                    total_mv, circ_mv,
                    data_source
                FROM stock_daily_quotes
                WHERE symbol = $1
                ORDER BY time DESC
                LIMIT 1
            """

            row = await execute_sql_one(query, symbol)

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"获取最新行情失败 symbol={symbol}: {e}")
            return None

    @staticmethod
    async def get_daily_quotes(
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取日K线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量

        Returns:
            K线数据列表
        """
        try:
            conditions = ["symbol = $1", "period = 'daily'"]
            params = [symbol]
            param_count = 1

            if start_date:
                param_count += 1
                conditions.append(f"time >= ${param_count}")
                params.append(start_date)

            if end_date:
                param_count += 1
                conditions.append(f"time <= ${param_count}")
                params.append(end_date)

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT
                    time, symbol, open, high, low, close, pre_close,
                    volume, amount, change, pct_chg,
                    turnover_rate, volume_ratio,
                    pe, pe_ttm, pb, total_mv, circ_mv
                FROM stock_daily_quotes
                WHERE {where_clause}
                ORDER BY time DESC
                LIMIT ${param_count + 1}
            """

            params.append(limit)
            rows = await execute_sql(query, *params)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"获取日K线失败 symbol={symbol}: {e}")
            return []

    @staticmethod
    async def get_moving_averages(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取移动平均线数据（使用窗口函数计算）

        Args:
            symbol: 股票代码
            days: 查询天数

        Returns:
            包含 MA5/10/20/60 的数据列表
        """
        try:
            query = """
                SELECT
                    time,
                    symbol,
                    close,
                    avg(close) OVER (
                        PARTITION BY symbol
                        ORDER BY time
                        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
                    ) AS ma_5,
                    avg(close) OVER (
                        PARTITION BY symbol
                        ORDER BY time
                        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                    ) AS ma_10,
                    avg(close) OVER (
                        PARTITION BY symbol
                        ORDER BY time
                        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
                    ) AS ma_20,
                    avg(close) OVER (
                        PARTITION BY symbol
                        ORDER BY time
                        ROWS BETWEEN 59 PRECEDING AND CURRENT ROW
                    ) AS ma_60
                FROM stock_daily_quotes
                WHERE symbol = $1 AND period = 'daily'
                    AND time >= CURRENT_DATE - INTERVAL '1 day' * $2
                ORDER BY time DESC
            """

            rows = await execute_sql(query, symbol, days)
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"获取移动平均线失败 symbol={symbol}: {e}")
            return []

    @staticmethod
    async def upsert_daily_quote(quote_data: Dict[str, Any]) -> bool:
        """
        插入或更新日K线数据

        Args:
            quote_data: K线数据字典

        Returns:
            成功返回 True
        """
        try:
            pool = get_pg_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO stock_daily_quotes (
                        time, symbol, open, high, low, close, pre_close,
                        volume, amount, change, pct_chg,
                        turnover_rate, volume_ratio,
                        pe, pe_ttm, pb, pb_mrq, ps,
                        dv_ratio, dv_ttm,
                        total_mv, circ_mv, adj_factor,
                        data_source, period
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18,
                        $19, $20, $21, $22, $23, $24, $25
                    )
                    ON CONFLICT (time, symbol, data_source, period) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        amount = EXCLUDED.amount,
                        pct_chg = EXCLUDED.pct_chg,
                        turnover_rate = EXCLUDED.turnover_rate,
                        pe = EXCLUDED.pe,
                        pb = EXCLUDED.pb,
                        total_mv = EXCLUDED.total_mv,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    quote_data.get('time'),
                    quote_data.get('symbol'),
                    quote_data.get('open'),
                    quote_data.get('high'),
                    quote_data.get('low'),
                    quote_data.get('close'),
                    quote_data.get('pre_close'),
                    quote_data.get('volume'),
                    quote_data.get('amount'),
                    quote_data.get('change'),
                    quote_data.get('pct_chg'),
                    quote_data.get('turnover_rate'),
                    quote_data.get('volume_ratio'),
                    quote_data.get('pe'),
                    quote_data.get('pe_ttm'),
                    quote_data.get('pb'),
                    quote_data.get('pb_mrq'),
                    quote_data.get('ps'),
                    quote_data.get('dv_ratio'),
                    quote_data.get('dv_ttm'),
                    quote_data.get('total_mv'),
                    quote_data.get('circ_mv'),
                    quote_data.get('adj_factor', 1.0),
                    quote_data.get('data_source'),
                    quote_data.get('period', 'daily')
                )

            return True

        except Exception as e:
            logger.error(f"保存K线数据失败: {e}")
            return False


# ============================================================================
# 财务数据服务
# ============================================================================

class FinancialDataService:
    """财务数据服务"""

    @staticmethod
    async def get_latest_financial(symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新财务数据

        Args:
            symbol: 股票代码

        Returns:
            最新财务数据
        """
        try:
            query = """
                SELECT
                    time, symbol, report_period, report_type, ann_date,
                    -- 资产负债表
                    total_assets, total_liab, total_equity,
                    total_cur_assets, total_nca,
                    total_cur_liab, total_ncl,
                    cash_and_equivalents,
                    -- 利润表
                    total_revenue, revenue, oper_cost,
                    gross_profit, oper_profit, total_profit,
                    net_income, net_income_attr_p,
                    basic_eps, diluted_eps,
                    -- 现金流量表
                    n_cashflow_act, n_cashflow_inv_act, n_cashflow_fin_act,
                    c_cash_equ_end, c_cash_equ_beg,
                    -- 财务指标
                    roe, roa, gross_margin, net_margin, netprofit_margin,
                    debt_to_assets, current_ratio, quick_ratio, bvps,
                    data_source
                FROM stock_financial_data
                WHERE symbol = $1
                ORDER BY time DESC
                LIMIT 1
            """

            row = await execute_sql_one(query, symbol)

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"获取最新财务数据失败 symbol={symbol}: {e}")
            return None

    @staticmethod
    async def get_financial_history(
        symbol: str,
        report_type: Optional[str] = None,
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        获取历史财务数据

        Args:
            symbol: 股票代码
            report_type: 报告类型（quarterly/annual）
            limit: 返回数量

        Returns:
            财务数据列表
        """
        try:
            conditions = ["symbol = $1"]
            params = [symbol]

            if report_type:
                conditions.append("report_type = $2")
                params.append(report_type)
                param_count = 2
            else:
                param_count = 1

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT
                    time, symbol, report_period, report_type,
                    total_revenue, net_income, net_income_attr_p,
                    roe, roa, gross_margin, net_margin,
                    basic_eps, bvps
                FROM stock_financial_data
                WHERE {where_clause}
                ORDER BY time DESC
                LIMIT ${param_count + 1}
            """

            params.append(limit)
            rows = await execute_sql(query, *params)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"获取财务历史失败 symbol={symbol}: {e}")
            return []

    @staticmethod
    async def upsert_financial_data(financial_data: Dict[str, Any]) -> bool:
        """
        插入或更新财务数据

        Args:
            financial_data: 财务数据字典

        Returns:
            成功返回 True
        """
        try:
            pool = get_pg_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO stock_financial_data (
                        time, symbol, report_period, report_type, ann_date,
                        total_assets, total_liab, total_equity,
                        total_cur_assets, total_nca, total_cur_liab, total_ncl,
                        cash_and_equivalents,
                        total_revenue, revenue, oper_cost,
                        gross_profit, oper_profit, total_profit,
                        net_income, net_income_attr_p,
                        basic_eps, diluted_eps,
                        n_cashflow_act, n_cashflow_inv_act, n_cashflow_fin_act,
                        c_cash_equ_end, c_cash_equ_beg,
                        roe, roa, gross_margin, net_margin, netprofit_margin,
                        debt_to_assets, current_ratio, quick_ratio, bvps,
                        data_source
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18,
                        $19, $20, $21, $22, $23, $24, $25, $26,
                        $27, $28, $29, $30, $31, $32, $33, $34,
                        $35, $36, $37
                    )
                    ON CONFLICT (time, symbol, report_period, data_source) DO UPDATE SET
                        total_revenue = EXCLUDED.total_revenue,
                        net_income = EXCLUDED.net_income,
                        net_income_attr_p = EXCLUDED.net_income_attr_p,
                        roe = EXCLUDED.roe,
                        roa = EXCLUDED.roa,
                        gross_margin = EXCLUDED.gross_margin,
                        net_margin = EXCLUDED.net_margin,
                        basic_eps = EXCLUDED.basic_eps,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    financial_data.get('time'),
                    financial_data.get('symbol'),
                    financial_data.get('report_period'),
                    financial_data.get('report_type'),
                    financial_data.get('ann_date'),
                    financial_data.get('total_assets'),
                    financial_data.get('total_liab'),
                    financial_data.get('total_equity'),
                    financial_data.get('total_cur_assets'),
                    financial_data.get('total_nca'),
                    financial_data.get('total_cur_liab'),
                    financial_data.get('total_ncl'),
                    financial_data.get('cash_and_equivalents'),
                    financial_data.get('total_revenue'),
                    financial_data.get('revenue'),
                    financial_data.get('oper_cost'),
                    financial_data.get('gross_profit'),
                    financial_data.get('oper_profit'),
                    financial_data.get('total_profit'),
                    financial_data.get('net_income'),
                    financial_data.get('net_income_attr_p'),
                    financial_data.get('basic_eps'),
                    financial_data.get('diluted_eps'),
                    financial_data.get('n_cashflow_act'),
                    financial_data.get('n_cashflow_inv_act'),
                    financial_data.get('n_cashflow_fin_act'),
                    financial_data.get('c_cash_equ_end'),
                    financial_data.get('c_cash_equ_beg'),
                    financial_data.get('roe'),
                    financial_data.get('roa'),
                    financial_data.get('gross_margin'),
                    financial_data.get('net_margin'),
                    financial_data.get('netprofit_margin'),
                    financial_data.get('debt_to_assets'),
                    financial_data.get('current_ratio'),
                    financial_data.get('quick_ratio'),
                    financial_data.get('bvps'),
                    financial_data.get('data_source')
                )

            return True

        except Exception as e:
            logger.error(f"保存财务数据失败: {e}")
            return False


# ============================================================================
# 导出服务实例
# ============================================================================

stock_info_service = StockInfoService()
market_quotes_service = MarketQuotesService()
financial_data_service = FinancialDataService()
