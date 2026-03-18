#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块 - Alpha Vantage + Yahoo Finance
更新：支持美股(Alpha Vantage)、港股(Yahoo)、汇率、加密货币

作者: 虾虾 🦐
"""

import requests
import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器"""

    def __init__(self, alpha_vantage_key: str = ""):
        """
        初始化

        Args:
            alpha_vantage_key: Alpha Vantage API Key
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.av_base = "https://www.alphavantage.co/query"

    # ==================== Alpha Vantage (美股) ====================

    def get_quote_av(self, symbol: str) -> Optional[dict]:
        """
        获取美股报价 (Alpha Vantage)

        Args:
            symbol: 股票代码 (如 AAPL, MSFT)

        Returns:
            dict: 报价数据
        """
        if not self.alpha_vantage_key:
            logger.warning("没有 Alpha Vantage API Key")
            return None

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_key
        }

        try:
            response = requests.get(self.av_base, params=params, timeout=10)
            data = response.json()
            quote = data.get("Global Quote", {})

            if not quote:
                return None

            return {
                "symbol": quote.get("01. symbol", ""),
                "price": float(quote.get("05. price", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_pct": quote.get("10. change percent", ""),
                "volume": int(quote.get("06. volume", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "open": float(quote.get("02. open", 0)),
                "source": "Alpha Vantage"
            }

        except Exception as e:
            logger.error(f"获取报价失败: {e}")
            return None

    def get_history_av(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        获取历史K线 (Alpha Vantage)

        Args:
            symbol: 股票代码
            days: 天数

        Returns:
            DataFrame: OHLCV数据
        """
        if not self.alpha_vantage_key:
            return pd.DataFrame()

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "output_size": "compact" if days <= 100 else "full",
            "apikey": self.alpha_vantage_key
        }

        try:
            response = requests.get(self.av_base, params=params, timeout=10)
            data = response.json()
            time_series = data.get("Time Series (Daily)", {})

            if not time_series:
                return pd.DataFrame()

            records = []
            for date, values in list(time_series.items())[:days]:
                records.append({
                    "Date": date,
                    "Open": float(values.get("1. open", 0)),
                    "High": float(values.get("2. high", 0)),
                    "Low": float(values.get("3. low", 0)),
                    "Close": float(values.get("4. close", 0)),
                    "Volume": int(values.get("5. volume", 0))
                })

            df = pd.DataFrame(records)
            df.set_index("Date", inplace=True)
            return df

        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()

    def get_forex_av(self, from_curr: str, to_curr: str) -> Optional[dict]:
        """
        获取汇率 (Alpha Vantage)

        Args:
            from_curr: 源货币 (如 USD)
            to_curr: 目标货币 (如 HKD)

        Returns:
            dict: 汇率数据
        """
        if not self.alpha_vantage_key:
            return None

        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_curr,
            "to_currency": to_curr,
            "apikey": self.alpha_vantage_key
        }

        try:
            response = requests.get(self.av_base, params=params, timeout=10)
            data = response.json()
            rate = data.get("Realtime Currency Exchange Rate", {})

            if not rate:
                return None

            return {
                "from": rate.get("1. From Currency Code", ""),
                "to": rate.get("3. To Currency Code", ""),
                "rate": float(rate.get("5. Exchange Rate", 0))
            }

        except Exception as e:
            logger.error(f"获取汇率失败: {e}")
            return None

    # ==================== Yahoo Finance (港股) ====================

    def get_quote_yf(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """
        获取港股报价 (Yahoo Finance)

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            dict: 报价数据
        """
        ticker = symbol
        if market == "hk":
            if symbol.isdigit():
                # 保持4位数字: 00700 -> 0700
                ticker = symbol.lstrip('0') or '0'
                ticker = ticker.zfill(4) + ".HK"
            elif not symbol.endswith(".HK"):
                ticker = f"{symbol}.HK"

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                "symbol": symbol,
                "price": info.get("currentPrice", info.get("previousClose", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("volume", 0),
                "high52w": info.get("fiftyTwoWeekHigh", 0),
                "low52w": info.get("fiftyTwoWeekLow", 0),
                "source": "Yahoo Finance"
            }

        except Exception as e:
            logger.error(f"获取报价失败: {e}")
            return None

    def get_history_yf(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        获取历史K线 (Yahoo Finance)

        Args:
            symbol: 股票代码
            period: 时间范围
            interval: K线周期

        Returns:
            DataFrame: OHLCV数据
        """
        try:
            ticker = symbol
            if not symbol.endswith(".HK"):
                ticker = f"{symbol}.HK"

            stock = yf.Ticker(ticker)
            return stock.history(period=period, interval=interval)

        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()

    # ==================== 统一接口 ====================

    def get_quote(self, symbol: str, market: str = "us") -> Optional[dict]:
        """
        获取报价 (自动选择数据源)

        Args:
            symbol: 股票代码
            market: 市场类型 (us/hk)

        Returns:
            dict: 报价数据
        """
        if market == "us":
            return self.get_quote_av(symbol)
        else:
            return self.get_quote_yf(symbol, market)

    def get_history(self, symbol: str, market: str = "us", days: int = 30, period: str = None) -> pd.DataFrame:
        """
        获取历史K线

        Args:
            symbol: 股票代码
            market: 市场类型
            days: 天数
            period: 时间范围（如 "1mo", "3mo", "1y"），优先于days

        Returns:
            DataFrame: OHLCV数据
        """
        # 如果指定了period，直接用
        if period:
            if market == "us":
                # 美股用 Alpha Vantage
                return self.get_history_av(symbol, days if days else 30)
            else:
                return self.get_history_yf(symbol, period=period)
        
        # 否则用 days
        if market == "us":
            return self.get_history_av(symbol, days)
        else:
            return self.get_history_yf(symbol, period=f"{days}d")

    def get_financials(self, symbol: str, market: str = "hk") -> Dict:
        """获取财务数据"""
        try:
            ticker = symbol
            if market == "hk":
                if symbol.isdigit():
                    ticker = symbol.lstrip('0') or '0'
                    ticker = ticker.zfill(4) + ".HK"
                    
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                "pe": info.get("trailingPE", 0),
                "market_cap": info.get("marketCap", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "beta": info.get("beta", 0),
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
            }
        except Exception as e:
            logger.error(f"获取财务数据失败 {symbol}: {e}")
            return {}

    def get_forex(self, from_curr: str = "USD", to_curr: str = "HKD") -> Optional[dict]:
        """
        获取汇率

        Args:
            from_curr: 源货币
            to_curr: 目标货币

        Returns:
            dict: 汇率
        """
        # 优先用 Alpha Vantage
        result = self.get_forex_av(from_curr, to_curr)
        if result:
            return result

        # 备用 Frankfurter
        return self.get_forex_frankfurter(from_curr, to_curr)

    def get_forex_frankfurter(self, from_curr: str, to_curr: str) -> Optional[dict]:
        """获取汇率 (Frankfurter API)"""
        try:
            url = f"https://api.frankfurter.app/latest?from={from_curr}&to={to_curr}"
            response = requests.get(url, timeout=10)
            data = response.json()
            rate = data.get("rates", {}).get(to_curr)

            if rate:
                return {
                    "from": from_curr,
                    "to": to_curr,
                    "rate": rate,
                    "source": "Frankfurter"
                }
        except Exception as e:
            logger.error(f"获取汇率失败: {e}")

        return None

    def get_crypto(self, symbol: str = "BTC") -> Optional[dict]:
        """获取加密货币价格"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()

            price = data.get(symbol.lower(), {}).get("usd")
            if price:
                return {
                    "symbol": symbol.upper(),
                    "price": price,
                    "currency": "USD",
                    "source": "CoinGecko"
                }
        except Exception as e:
            logger.error(f"获取加密货币失败: {e}")

        return None


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # Alpha Vantage Key
    API_KEY = "168S7Z8WRRUG3GIQ"

    fetcher = DataFetcher(API_KEY)

    # 测试美股
    print("=== 美股 (Alpha Vantage) ===")
    quote = fetcher.get_quote("AAPL", "us")
    if quote:
        print(f"{quote['symbol']}: ${quote['price']} ({quote['change_pct']})")

    # 测试港股
    print("\n=== 港股 (Yahoo Finance) ===")
    quote = fetcher.get_quote("00700", "hk")
    if quote:
        print(f"{quote['symbol']}: ${quote['price']}")

    # 测试汇率
    print("\n=== 汇率 ===")
    rate = fetcher.get_forex("USD", "HKD")
    if rate:
        print(f"1 {rate['from']} = {rate['rate']} {rate['to']} ({rate['source']})")

    # 测试加密货币
    print("\n=== 加密货币 ===")
    crypto = fetcher.get_crypto("BTC")
    if crypto:
        print(f"{crypto['symbol']}: ${crypto['price']}")
