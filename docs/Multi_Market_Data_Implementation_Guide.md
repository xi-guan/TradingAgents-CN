# 多市场数据支持实现指南
# Multi-Market Data Support Implementation Guide

> **目的**: 解释 TradingAgents-CN 如何实现 A股、港股、美股三大市场的数据支持
> **难度评估**: 中等 - 需要理解数据源API和数据标准化
> **时间估算**: 2-4周 (取决于对数据源的熟悉程度)

---

## 📋 目录

1. [整体架构](#1-整体架构)
2. [数据源选择](#2-数据源选择)
3. [实现难点](#3-实现难点)
4. [具体实现步骤](#4-具体实现步骤)
5. [代码实现示例](#5-代码实现示例)
6. [成本分析](#6-成本分析)
7. [实施建议](#7-实施建议)

---

## 1. 整体架构

### 1.1 数据流架构

```
用户请求
    ↓
市场识别 (A股/美股/港股)
    ↓
数据源管理器 (DataSourceManager)
    ↓
    ├─→ MongoDB缓存 (优先)
    ├─→ A股数据源 (Tushare/AKShare/BaoStock)
    ├─→ 美股数据源 (yfinance/Finnhub/Alpha Vantage)
    └─→ 港股数据源 (AKShare/yfinance)
    ↓
数据标准化
    ↓
返回统一格式数据
```

### 1.2 目录结构

```
tradingagents/
├── dataflows/
│   ├── data_source_manager.py     # 数据源管理器
│   ├── providers/                  # 各市场数据提供商
│   │   ├── china/                  # A股数据源
│   │   │   ├── tushare.py         # Tushare实现
│   │   │   ├── akshare.py         # AKShare实现
│   │   │   └── baostock.py        # BaoStock实现
│   │   ├── us/                     # 美股数据源
│   │   │   ├── yfinance.py        # yfinance实现
│   │   │   ├── finnhub.py         # Finnhub实现
│   │   │   └── alpha_vantage.py   # Alpha Vantage实现
│   │   └── hk/                     # 港股数据源
│   │       ├── hk_stock.py        # 港股主实现
│   │       └── improved_hk.py     # 增强港股实现
│   └── cache/                      # 缓存层
│       └── mongodb_cache.py
└── constants/
    └── data_sources.py             # 数据源注册表
```

---

## 2. 数据源选择

### 2.1 A股数据源

#### 推荐组合 (免费)
```
主数据源: Tushare (需注册，有免费额度)
备用数据源: AKShare (完全免费)
降级数据源: BaoStock (完全免费)
```

#### 数据源对比

| 数据源 | 优点 | 缺点 | 成本 | 推荐指数 |
|--------|------|------|------|---------|
| **Tushare** | 数据质量高，更新及时，专业 | 免费版有调用限制 | 免费版/专业版¥500+/年 | ⭐⭐⭐⭐⭐ |
| **AKShare** | 完全免费，无需注册，数据全 | 稳定性一般，无官方支持 | 免费 | ⭐⭐⭐⭐ |
| **BaoStock** | 免费，数据稳定 | 更新较慢，功能有限 | 免费 | ⭐⭐⭐ |

#### 关键API示例

**Tushare**:
```python
import tushare as ts

# 初始化
ts.set_token('YOUR_TOKEN')
pro = ts.pro_api()

# 获取日线数据
df = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20241231')

# 获取财务数据
df_finance = pro.income(ts_code='000001.SZ', period='20231231')

# 获取实时行情
df_rt = pro.query('daily', ts_code='000001.SZ', trade_date='20241115')
```

**AKShare**:
```python
import akshare as ak

# 获取历史行情
df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20241231")

# 获取实时行情
df_rt = ak.stock_zh_a_spot_em()

# 获取财务数据
df_finance = ak.stock_financial_analysis_indicator(symbol="000001")
```

### 2.2 美股数据源

#### 推荐组合 (免费)
```
主数据源: yfinance (完全免费，Yahoo Finance)
备用数据源: Finnhub (有免费API)
高级数据: Alpha Vantage (技术指标)
```

#### 数据源对比

| 数据源 | 优点 | 缺点 | 成本 | 推荐指数 |
|--------|------|------|------|---------|
| **yfinance** | 完全免费，易用，数据全 | 非官方API，可能被限流 | 免费 | ⭐⭐⭐⭐⭐ |
| **Finnhub** | 实时数据，新闻丰富 | 免费版有限制 | 免费版/付费版 | ⭐⭐⭐⭐ |
| **Alpha Vantage** | 技术指标丰富 | 免费版每分钟5次调用 | 免费版/付费版 | ⭐⭐⭐ |

#### 关键API示例

**yfinance**:
```python
import yfinance as yf

# 获取股票信息
ticker = yf.Ticker("AAPL")

# 获取历史数据
df = ticker.history(start="2024-01-01", end="2024-12-31")

# 获取财务数据
financials = ticker.financials
balance_sheet = ticker.balance_sheet
cash_flow = ticker.cashflow

# 获取实时数据
current_price = ticker.info['currentPrice']
```

**Finnhub**:
```python
import finnhub

# 初始化
finnhub_client = finnhub.Client(api_key="YOUR_API_KEY")

# 获取报价
quote = finnhub_client.quote('AAPL')

# 获取K线数据
candles = finnhub_client.stock_candles('AAPL', 'D', 1590988249, 1591852249)

# 获取公司基本面
profile = finnhub_client.company_profile2(symbol='AAPL')

# 获取新闻
news = finnhub_client.company_news('AAPL', _from="2024-01-01", to="2024-12-31")
```

### 2.3 港股数据源

#### 推荐组合
```
主数据源: yfinance (支持港股，代码格式: 0700.HK)
备用数据源: AKShare (支持港股)
专业数据: 新浪财经API
```

#### 数据源对比

| 数据源 | 优点 | 缺点 | 成本 | 推荐指数 |
|--------|------|------|------|---------|
| **yfinance** | 免费，全球市场支持 | 港股数据有时延迟 | 免费 | ⭐⭐⭐⭐ |
| **AKShare** | 免费，中文友好 | 港股数据不如A股全 | 免费 | ⭐⭐⭐⭐ |
| **新浪财经** | 数据更新快 | 非官方API | 免费 | ⭐⭐⭐ |

#### 关键API示例

**yfinance (港股)**:
```python
import yfinance as yf

# 港股代码格式: {code}.HK
ticker = yf.Ticker("0700.HK")  # 腾讯控股

# 获取历史数据
df = ticker.history(start="2024-01-01", end="2024-12-31")

# 获取财务数据
financials = ticker.financials
```

**AKShare (港股)**:
```python
import akshare as ak

# 获取港股实时行情
df_hk = ak.stock_hk_spot_em()

# 获取历史行情
df_hist = ak.stock_hk_hist(symbol="00700", period="daily", start_date="20240101", end_date="20241231")
```

---

## 3. 实现难点

### 3.1 难点分析

| 难点 | 难度 | 解决方法 |
|------|------|---------|
| **股票代码格式不统一** | ⭐⭐⭐ | 建立代码映射表，标准化处理 |
| **数据字段名称不统一** | ⭐⭐⭐⭐ | 字段映射，统一数据模型 |
| **数据单位不统一** | ⭐⭐⭐ | 单位转换，标准化 |
| **API限流和稳定性** | ⭐⭐⭐⭐ | 多数据源降级，缓存机制 |
| **货币单位差异** | ⭐⭐ | 记录货币类型，显示时转换 |
| **交易时间和时区** | ⭐⭐⭐ | 时区转换，统一为UTC+8 |

### 3.2 股票代码标准化

#### 问题
不同市场和数据源的代码格式不一致:

```
A股:
- Tushare: 000001.SZ, 600000.SH
- AKShare: 000001, 600000
- BaoStock: sz.000001, sh.600000

美股:
- yfinance: AAPL, TSLA
- Finnhub: AAPL, TSLA

港股:
- yfinance: 0700.HK, 0388.HK
- AKShare: 00700, 00388
```

#### 解决方案

```python
class StockCodeNormalizer:
    """股票代码标准化器"""

    @staticmethod
    def normalize(code: str, market: str, provider: str = None) -> str:
        """
        标准化股票代码

        Args:
            code: 原始股票代码
            market: 市场 (A, US, HK)
            provider: 数据提供商 (可选)

        Returns:
            标准化后的代码
        """
        if market == "A":
            # A股标准化为: 000001.SZ, 600000.SH
            code = code.upper().replace('SZ.', '').replace('SH.', '')

            if '.' not in code:
                # 判断市场
                if code.startswith('6'):
                    return f"{code}.SH"
                else:
                    return f"{code}.SZ"
            return code

        elif market == "US":
            # 美股直接大写
            return code.upper()

        elif market == "HK":
            # 港股标准化为: 0700.HK
            code = code.replace('.HK', '')
            code = code.zfill(5)  # 补齐5位
            return f"{code}.HK"

        return code
```

### 3.3 数据字段标准化

#### 问题
不同数据源返回的字段名不同:

```python
# Tushare返回
{
    'ts_code': '000001.SZ',
    'trade_date': '20241115',
    'close': 12.50,
    'pct_chg': 2.5,
    'vol': 1000000,  # 单位: 手
    'amount': 125000000  # 单位: 千元
}

# AKShare返回
{
    '股票代码': '000001',
    '日期': '2024-11-15',
    '收盘': 12.50,
    '涨跌幅': 2.5,
    '成交量': 100000000,  # 单位: 股
    '成交额': 125000000  # 单位: 元
}

# yfinance返回
{
    'Date': '2024-11-15',
    'Close': 12.50,
    'Volume': 1000000,
    'Change%': 2.5
}
```

#### 解决方案

**方法1: 字段映射表**
```python
FIELD_MAPPING = {
    'tushare': {
        'ts_code': 'symbol',
        'trade_date': 'date',
        'close': 'close',
        'pct_chg': 'change_pct',
        'vol': 'volume',
        'amount': 'amount',
    },
    'akshare': {
        '股票代码': 'symbol',
        '日期': 'date',
        '收盘': 'close',
        '涨跌幅': 'change_pct',
        '成交量': 'volume',
        '成交额': 'amount',
    },
    'yfinance': {
        'Date': 'date',
        'Close': 'close',
        'Volume': 'volume',
        'Change%': 'change_pct',
    }
}

def standardize_dataframe(df: pd.DataFrame, provider: str) -> pd.DataFrame:
    """标准化DataFrame字段"""
    mapping = FIELD_MAPPING.get(provider, {})
    df = df.rename(columns=mapping)

    # 单位转换
    if provider == 'tushare':
        df['volume'] = df['volume'] * 100  # 手 -> 股
        df['amount'] = df['amount'] * 1000  # 千元 -> 元

    return df
```

**方法2: 统一数据模型**
```python
from dataclasses import dataclass
from datetime import date

@dataclass
class StockQuote:
    """统一的股票报价数据模型"""
    symbol: str           # 股票代码 (标准化格式)
    date: date           # 日期
    open: float          # 开盘价
    high: float          # 最高价
    low: float           # 最低价
    close: float         # 收盘价
    volume: int          # 成交量 (股)
    amount: float        # 成交额 (元)
    change: float        # 涨跌额
    change_pct: float    # 涨跌幅 (%)

    # 可选字段
    turnover_rate: float = None  # 换手率
    pe_ratio: float = None       # 市盈率
    pb_ratio: float = None       # 市净率
```

---

## 4. 具体实现步骤

### 步骤1: 安装数据源库

```bash
# A股数据源
pip install tushare
pip install akshare
pip install baostock

# 美股数据源
pip install yfinance
pip install finnhub-python
pip install alpha_vantage

# 通用工具
pip install pandas numpy
pip install pymongo  # MongoDB缓存
```

### 步骤2: 创建基础数据提供商接口

```python
# tradingagents/dataflows/providers/base_provider.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
from datetime import date

class BaseStockDataProvider(ABC):
    """股票数据提供商基类"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"provider.{name}")

    @abstractmethod
    def connect(self) -> bool:
        """连接到数据源"""
        pass

    @abstractmethod
    def get_daily_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        pass

    @abstractmethod
    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价"""
        pass

    @abstractmethod
    def get_financials(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        pass
```

### 步骤3: 实现各市场数据提供商

#### A股 - Tushare实现

```python
# tradingagents/dataflows/providers/china/tushare.py

import tushare as ts
from ..base_provider import BaseStockDataProvider

class TushareProvider(BaseStockDataProvider):
    """Tushare数据提供商"""

    def __init__(self, token: str = None):
        super().__init__("Tushare")
        self.token = token or os.getenv('TUSHARE_TOKEN')
        self.api = None

    def connect(self) -> bool:
        """连接到Tushare"""
        try:
            ts.set_token(self.token)
            self.api = ts.pro_api()
            return True
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False

    def get_daily_quotes(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """获取日线数据"""
        # 转换代码格式
        ts_code = self._to_tushare_code(symbol)

        # 获取数据
        df = self.api.daily(
            ts_code=ts_code,
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )

        # 标准化数据
        df = self._standardize_daily_data(df)
        return df

    def _to_tushare_code(self, symbol: str) -> str:
        """转换为Tushare代码格式"""
        # 000001 -> 000001.SZ
        # 600000 -> 600000.SH
        if '.' not in symbol:
            if symbol.startswith('6'):
                return f"{symbol}.SH"
            else:
                return f"{symbol}.SZ"
        return symbol

    def _standardize_daily_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化日线数据"""
        # 字段映射
        df = df.rename(columns={
            'ts_code': 'symbol',
            'trade_date': 'date',
            'close': 'close',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'vol': 'volume',
            'amount': 'amount',
            'pct_chg': 'change_pct',
            'change': 'change',
        })

        # 单位转换
        df['volume'] = df['volume'] * 100  # 手 -> 股
        df['amount'] = df['amount'] * 1000  # 千元 -> 元

        # 日期格式转换
        df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')

        return df
```

#### 美股 - yfinance实现

```python
# tradingagents/dataflows/providers/us/yfinance.py

import yfinance as yf
from ..base_provider import BaseStockDataProvider

class YFinanceProvider(BaseStockDataProvider):
    """yfinance数据提供商"""

    def __init__(self):
        super().__init__("yfinance")

    def connect(self) -> bool:
        """yfinance无需连接"""
        return True

    def get_daily_quotes(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """获取日线数据"""
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        # 标准化数据
        df = self._standardize_daily_data(df, symbol)
        return df

    def _standardize_daily_data(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """标准化日线数据"""
        df = df.reset_index()

        # 字段映射
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        })

        # 添加symbol
        df['symbol'] = symbol

        # 计算涨跌
        df['change'] = df['close'] - df['close'].shift(1)
        df['change_pct'] = (df['change'] / df['close'].shift(1)) * 100

        # 成交额估算 (价格 * 成交量)
        df['amount'] = df['close'] * df['volume']

        return df
```

### 步骤4: 实现数据源管理器

```python
# tradingagents/dataflows/data_source_manager.py

class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        self.providers = {
            'A': {
                'primary': TushareProvider(),
                'fallback': [AKShareProvider(), BaoStockProvider()],
            },
            'US': {
                'primary': YFinanceProvider(),
                'fallback': [FinnhubProvider(), AlphaVantageProvider()],
            },
            'HK': {
                'primary': YFinanceProvider(),
                'fallback': [AKShareProvider()],
            }
        }

        # MongoDB缓存
        self.cache = MongoDBCache()

    def get_daily_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        market: str = None
    ) -> pd.DataFrame:
        """
        获取日线数据（带缓存和降级）

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            market: 市场类型 (A/US/HK)，不指定则自动识别

        Returns:
            标准化的DataFrame
        """
        # 自动识别市场
        if not market:
            market = self._identify_market(symbol)

        # 1. 尝试从缓存获取
        cached_data = self.cache.get_daily_quotes(symbol, start_date, end_date)
        if cached_data is not None:
            self.logger.info(f"✅ 从缓存获取数据: {symbol}")
            return cached_data

        # 2. 从主数据源获取
        providers = self.providers[market]
        primary_provider = providers['primary']

        try:
            data = primary_provider.get_daily_quotes(symbol, start_date, end_date)
            if not data.empty:
                # 保存到缓存
                self.cache.save_daily_quotes(symbol, data)
                self.logger.info(f"✅ 从主数据源获取: {primary_provider.name}")
                return data
        except Exception as e:
            self.logger.warning(f"⚠️ 主数据源失败: {e}")

        # 3. 尝试降级数据源
        for fallback_provider in providers['fallback']:
            try:
                data = fallback_provider.get_daily_quotes(symbol, start_date, end_date)
                if not data.empty:
                    self.cache.save_daily_quotes(symbol, data)
                    self.logger.info(f"✅ 从降级数据源获取: {fallback_provider.name}")
                    return data
            except Exception as e:
                self.logger.warning(f"⚠️ 降级数据源失败: {fallback_provider.name}: {e}")

        # 4. 所有数据源都失败
        self.logger.error(f"❌ 所有数据源都失败: {symbol}")
        return pd.DataFrame()

    def _identify_market(self, symbol: str) -> str:
        """识别股票市场"""
        symbol = symbol.upper()

        # 港股
        if '.HK' in symbol or (symbol.isdigit() and len(symbol) == 5):
            return 'HK'

        # A股
        if '.SZ' in symbol or '.SH' in symbol or '.BJ' in symbol:
            return 'A'
        if symbol.isdigit() and len(symbol) == 6:
            return 'A'

        # 美股 (默认)
        return 'US'
```

### 步骤5: MongoDB缓存实现

```python
# tradingagents/dataflows/cache/mongodb_cache.py

from pymongo import MongoClient
import pandas as pd
from datetime import date

class MongoDBCache:
    """MongoDB缓存"""

    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['tradingagents']
        self.collection = self.db['stock_daily_quotes']

        # 创建索引
        self.collection.create_index([('symbol', 1), ('date', 1)], unique=True)

    def get_daily_quotes(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """从缓存获取日线数据"""
        query = {
            'symbol': symbol,
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }

        cursor = self.collection.find(query)
        data = list(cursor)

        if not data:
            return None

        df = pd.DataFrame(data)
        df = df.drop('_id', axis=1)  # 删除MongoDB的_id字段
        return df

    def save_daily_quotes(self, symbol: str, df: pd.DataFrame):
        """保存日线数据到缓存"""
        records = df.to_dict('records')

        for record in records:
            self.collection.update_one(
                {'symbol': symbol, 'date': record['date']},
                {'$set': record},
                upsert=True
            )
```

---

## 5. 代码实现示例

### 完整使用示例

```python
from tradingagents.dataflows import DataSourceManager
from datetime import date

# 初始化数据源管理器
manager = DataSourceManager()

# 获取A股数据
df_a = manager.get_daily_quotes(
    symbol='000001',  # 平安银行
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    market='A'
)
print(df_a.head())

# 获取美股数据
df_us = manager.get_daily_quotes(
    symbol='AAPL',  # 苹果
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    market='US'
)
print(df_us.head())

# 获取港股数据
df_hk = manager.get_daily_quotes(
    symbol='0700',  # 腾讯控股
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31),
    market='HK'
)
print(df_hk.head())
```

---

## 6. 成本分析

### 6.1 免费方案

完全免费的组合 (适合个人学习):

```
A股: AKShare (免费) + BaoStock (免费)
美股: yfinance (免费)
港股: yfinance (免费) + AKShare (免费)

总成本: ¥0/月
优点: 零成本，易于上手
缺点: 数据质量和稳定性一般，有限流风险
```

### 6.2 低成本方案

少量付费 (适合小团队):

```
A股: Tushare (¥500/年) + AKShare备用
美股: yfinance + Finnhub免费版
港股: yfinance + AKShare备用

总成本: ¥500/年 ≈ ¥42/月
优点: 性价比高，数据质量好
缺点: Tushare免费版有调用限制
```

### 6.3 专业方案

专业数据服务 (适合企业):

```
A股: Tushare专业版 (¥5000/年) 或 Wind (¥数万/年)
美股: Finnhub付费版 (¥200/月) + IEX Cloud
港股: Wind 或 付费数据服务

总成本: ¥5000-50000/年
优点: 数据全面，质量高，稳定
缺点: 成本高
```

---

## 7. 实施建议

### 7.1 推荐实施路径

**阶段1: MVP (1周)**
- ✅ 只实现A股支持
- ✅ 使用AKShare (免费)
- ✅ 简单的数据标准化
- ✅ 无缓存

**阶段2: 基础版 (2周)**
- ✅ 添加美股、港股支持
- ✅ 使用yfinance (免费)
- ✅ 完整的数据标准化
- ✅ 文件缓存

**阶段3: 完整版 (3-4周)**
- ✅ 多数据源支持
- ✅ 数据源降级策略
- ✅ MongoDB缓存
- ✅ 错误处理和重试

**阶段4: 专业版 (持续优化)**
- ✅ 付费数据源集成
- ✅ 实时数据推送
- ✅ 数据质量监控
- ✅ 性能优化

### 7.2 难度评估

| 功能模块 | 难度 | 时间估算 | 必要性 |
|---------|------|---------|-------|
| 数据源接口实现 | ⭐⭐⭐ | 3-5天 | 必须 |
| 数据标准化 | ⭐⭐⭐⭐ | 2-3天 | 必须 |
| 缓存系统 | ⭐⭐⭐ | 2-3天 | 重要 |
| 降级策略 | ⭐⭐ | 1-2天 | 重要 |
| 市场识别 | ⭐⭐ | 1天 | 必须 |
| 代码标准化 | ⭐⭐⭐ | 1-2天 | 必须 |
| 错误处理 | ⭐⭐ | 1-2天 | 重要 |

### 7.3 常见坑和解决方案

#### 坑1: API限流
**问题**: 免费API通常有调用频率限制
**解决**:
- 使用缓存减少API调用
- 添加请求延迟 (time.sleep)
- 实现请求队列
- 准备多个备用API Key

#### 坑2: 数据质量不一致
**问题**: 不同数据源数据有差异
**解决**:
- 优先使用高质量数据源
- 数据验证和清洗
- 异常值检测
- 交叉验证

#### 坑3: 时区问题
**问题**: 不同市场时区不同
**解决**:
```python
# 统一转换为UTC+8
df['date'] = pd.to_datetime(df['date']).dt.tz_localize('UTC').dt.tz_convert('Asia/Shanghai')
```

#### 坑4: 港股代码格式
**问题**: 港股代码有多种格式 (700, 0700, 00700)
**解决**:
```python
def normalize_hk_code(code: str) -> str:
    """港股代码标准化为5位"""
    code = code.replace('.HK', '')
    code = code.zfill(5)  # 补齐到5位
    return f"{code}.HK"
```

---

## 8. 总结

### 8.1 实现难度总结

✅ **容易实现的部分** (1-2周):
- 单一数据源集成 (如只用yfinance)
- 基础数据获取 (日线、实时)
- 简单的数据标准化

⚠️ **中等难度部分** (2-3周):
- 多数据源管理和切换
- 完整的数据标准化
- 缓存系统
- 三个市场同时支持

🔴 **复杂部分** (3-4周+):
- 数据质量保证
- 高级缓存策略
- 实时数据推送
- 性能优化

### 8.2 最小可行方案 (MVP)

如果你想快速实现基本功能:

```python
# 1. 安装依赖
pip install yfinance akshare pandas

# 2. 简单实现
import yfinance as yf
import akshare as ak

def get_stock_data(symbol, market='US'):
    """简单的多市场数据获取"""

    if market == 'A':
        # A股使用AKShare
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date="20240101",
            end_date="20241231"
        )
    elif market == 'US':
        # 美股使用yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(start="2024-01-01", end="2024-12-31")
    elif market == 'HK':
        # 港股使用yfinance
        ticker = yf.Ticker(f"{symbol}.HK")
        df = ticker.history(start="2024-01-01", end="2024-12-31")

    return df

# 使用示例
df_a = get_stock_data('000001', market='A')   # A股
df_us = get_stock_data('AAPL', market='US')   # 美股
df_hk = get_stock_data('0700', market='HK')   # 港股
```

这个MVP方案只需要**2-3天**就能实现，虽然功能简单但已经可以用了。

---

## 附录

### A. 数据源API获取

- **Tushare**: https://tushare.pro/register
- **AKShare**: 无需注册，直接使用
- **Finnhub**: https://finnhub.io/register
- **Alpha Vantage**: https://www.alphavantage.co/support/#api-key

### B. 参考资源

- **Tushare文档**: https://tushare.pro/document/2
- **AKShare文档**: https://akshare.akfamily.xyz/
- **yfinance文档**: https://pypi.org/project/yfinance/
- **Finnhub文档**: https://finnhub.io/docs/api

### C. 完整代码仓库

参考 TradingAgents-CN 的实现 (仅供学习，独立实现):
- `tradingagents/dataflows/providers/`
- `tradingagents/dataflows/data_source_manager.py`
- `tradingagents/constants/data_sources.py`

---

**祝你实现顺利！** 🎉

如有问题，欢迎交流讨论。
