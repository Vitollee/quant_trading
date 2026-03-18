#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alpha Vantage API 数据获取
支持美股、港股(部分)、外汇、加密货币

作者: 虾虾 🦐
"""

import requests
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlphaVantageAPI:
    """Alpha Vantage API 客户端"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        """
        初始化

        Args:
            api_key: Alpha Vantage API Key
        """
        self.api_key = api_key

    def quote(self, symbol: str) -> Optional[Dict]:
        """
        获取实时报价

        Args:
            symbol: 股票代码 (如 AAPL, MSFT)

        Returns:
            dict: 报价数据
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            quote = data.get("Global Quote", {})

            if not quote:
                logger.warning(f"没有数据: {symbol}")
                return None

            return {
                "symbol": quote.get("01. symbol", ""),
                "price": float(quote.get("05. price", 0)),
                "open": float(quote.get("02. open", 0)),
                "high": float(quote.get("03. high", 0)),
                "low": float(quote.get("04. low", 0)),
                "volume": int(quote.get("06. volume", 0)),
                "change": float(quote.get("09. change", 0)),
                "change_pct": quote.get("10. change percent", ""),
                "last_trading_day": quote.get("07. latest trading day", "")
            }

        except Exception as e:
            logger.error(f"获取报价失败 {symbol}: {e}")
            return None

    def intraday(self, symbol: str, interval: str = "5min") -> Optional[Dict]:
        """
        获取日内分钟数据

        Args:
            symbol: 股票代码
            interval: 分钟间隔 (1min, 5min, 15min, 30min, 60min)

        Returns:
            dict: K线数据
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            time_series = data.get(f"Time Series ({interval})", {})

            if not time_series:
                return None

            # 取最新5条数据
            results = []
            for i, (datetime_str, values) in enumerate(list(time_series.items())[:5]):
                results.append({
                    "datetime": datetime_str,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })

            return {
                "symbol": symbol,
                "interval": interval,
                "data": results
            }

        except Exception as e:
            logger.error(f"获取日内数据失败 {symbol}: {e}")
            return None

    def daily(self, symbol: str, output_size: str = "compact") -> Optional[Dict]:
        """
        获取日K线数据

        Args:
            symbol: 股票代码
            output_size: compact(100天) 或 full(完整历史)

        Returns:
            dict: 日K数据
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "output_size": output_size,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            time_series = data.get("Time Series (Daily)", {})

            if not time_series:
                return None

            results = []
            for i, (date, values) in enumerate(list(time_series.items())[:30]):
                results.append({
                    "date": date,
                    "open": float(values.get("1. open", 0)),
                    "high": float(values.get("2. high", 0)),
                    "low": float(values.get("3. low", 0)),
                    "close": float(values.get("4. close", 0)),
                    "volume": int(values.get("5. volume", 0))
                })

            return {
                "symbol": symbol,
                "data": results
            }

        except Exception as e:
            logger.error(f"获取日K数据失败 {symbol}: {e}")
            return None

    def forex(self, from_currency: str, to_currency: str) -> Optional[Dict]:
        """
        获取汇率

        Args:
            from_currency: 源货币 (如 USD, EUR)
            to_currency: 目标货币 (如 HKD, CNY)

        Returns:
            dict: 汇率数据
        """
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
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

    def crypto(self, symbol: str, market: str = "USD") -> Optional[Dict]:
        """
        获取加密货币价格

        Args:
            symbol: 加密货币代码 (如 BTC, ETH)
            market: 市场货币 (默认 USD)

        Returns:
            dict: 加密货币数据
        """
        params = {
            "function": "CRYPTO_RATING",
            "symbol": symbol,
            "market": market,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()

            crypto_data = data.get("Crypto Rating", {})

            if not crypto_data:
                return None

            return {
                "symbol": crypto_data.get("symbol", ""),
                "name": crypto_data.get("name", ""),
                "rating": crypto_data.get("digital currency rating", ""),
                "price": crypto_data.get("price (USD)", "")
            }

        except Exception as e:
            logger.error(f"获取加密货币失败: {e}")
            return None


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 你的 API Key
    API_KEY = "168S7Z8WRRUG3GIQ"

    av = AlphaVantageAPI(API_KEY)

    # 测试美股
    print("=== Apple 报价 ===")
    quote = av.quote("AAPL")
    if quote:
        print(f"{quote['symbol']}: ${quote['price']}")
        print(f"涨跌: {quote['change']} ({quote['change_pct']})")

    print("\n=== 汇率 USD to HKD ===")
    rate = av.forex("USD", "HKD")
    if rate:
        print(f"1 {rate['from']} = {rate['rate']} {rate['to']}")

    print("\n=== BTC 加密货币 ===")
    btc = av.crypto("BTC")
    if btc:
        print(f"{btc['symbol']}: {btc['price']}")
