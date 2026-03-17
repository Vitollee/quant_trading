#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块
功能: 从Yahoo Finance获取港股和美股行情数据
作者: 虾虾 🦐
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器"""

    def __init__(self):
        """初始化"""
        self.cache = {}  # 数据缓存

    def get_quote(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """
        获取单只股票实时行情

        Args:
            symbol: 股票代码 (如 00700 或 AAPL)
            market: 市场类型 "hk" 或 "us"

        Returns:
            dict: 包含价格、涨跌幅等信息的字典
        """
        # 转换代码格式
        ticker = self._format_symbol(symbol, market)

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            quote = {
                "symbol": symbol,
                "market": market,
                "name": info.get("shortName", info.get("longName", "N/A")),
                "price": info.get("currentPrice", info.get("previousClose", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "pe": info.get("trailingPE", 0),
                "pb": info.get("priceToBook", 0),
                "high52w": info.get("fiftyTwoWeekHigh", 0),
                "low52w": info.get("fiftyTwoWeekLow", 0),
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"获取行情成功: {symbol} = {quote['price']}")
            return quote

        except Exception as e:
            logger.error(f"获取行情失败 {symbol}: {e}")
            return None

    def get_history(self, symbol: str, market: str = "hk",
                    period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            market: 市场类型
            period: 时间范围 (1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max)
            interval: K线周期 (1m, 5m, 15m, 1h, 1d, 1wk, 1mo)

        Returns:
            DataFrame: OHLCV数据
        """
        ticker = self._format_symbol(symbol, market)

        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                logger.warning(f"无数据: {symbol}")
                return pd.DataFrame()

            logger.info(f"获取历史数据: {symbol}, {len(df)}条")
            return df

        except Exception as e:
            logger.error(f"获取历史数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def get_quotes_batch(self, symbols: List[str], market: str = "hk") -> Dict[str, dict]:
        """
        批量获取多只股票行情

        Args:
            symbols: 股票代码列表
            market: 市场类型

        Returns:
            dict: symbol -> quote
        """
        results = {}

        for symbol in symbols:
            quote = self.get_quote(symbol, market)
            if quote:
                results[symbol] = quote

        return results

    def get_financials(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """
        获取财务数据

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            dict: 财务指标
        """
        ticker = self._format_symbol(symbol, market)

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            financials = {
                # 估值指标
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "ps_ratio": info.get("priceToSales", 0),
                "market_cap": info.get("marketCap", 0),

                # 盈利能力
                "roe": info.get("returnOnEquity", 0),  # ROE
                "roa": info.get("returnOnAssets", 0),  # ROA
                "gross_margin": info.get("grossMargins", 0),  # 毛利率
                "operating_margin": info.get("operatingMargins", 0),  # 营业利润率

                # 成长性
                "revenue_growth": info.get("revenueGrowth", 0),  # 营收增长
                "earnings_growth": info.get("earningsGrowth", 0),  # 盈利增长
                "eps": info.get("trailingEps", 0),  # 每股收益

                # 资产负债
                "debt_to_equity": info.get("debtToEquity", 0),  # 资产负债率
                "current_ratio": info.get("currentRatio", 0),  # 流动比率
            }

            return financials

        except Exception as e:
            logger.error(f"获取财务数据失败 {symbol}: {e}")
            return None

    def _format_symbol(self, symbol: str, market: str) -> str:
        """
        格式化股票代码为Yahoo Finance格式

        Args:
            symbol: 原始代码
            market: 市场类型

        Returns:
            str: 格式化后的代码
        """
        symbol = symbol.strip().upper()

        if market == "hk":
            # 港股: 添加.HK后缀
            if not symbol.endswith(".HK"):
                if symbol.isdigit():
                    # 数字代码直接加.HK
                    return f"{symbol}.HK"
                else:
                    # 已经是有代码的直接返回
                    return symbol
            return symbol

        elif market == "us":
            # 美股: 保持原样
            return symbol

        return symbol


# ==================== 测试代码 ====================
if __name__ == "__main__":
    fetcher = DataFetcher()

    # 测试获取单只股票
    print("=== 测试获取腾讯 ===")
    quote = fetcher.get_quote("00700", "hk")
    if quote:
        print(f"名称: {quote['name']}")
        print(f"价格: {quote['price']}")
        print(f"涨跌: {quote['change']:.2f} ({quote['change_pct']:.2f}%)")

    print("\n=== 测试获取美股 ===")
    quote = fetcher.get_quote("AAPL", "us")
    if quote:
        print(f"名称: {quote['name']}")
        print(f"价格: ${quote['price']}")

    print("\n=== 测试获取历史数据 ===")
    df = fetcher.get_history("00700", "hk", period="1mo")
    print(f"获取到 {len(df)} 条K线数据")
    if not df.empty:
        print(df.tail())
