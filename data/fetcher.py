#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块 - 富途 + Alpha Vantage + Yahoo Finance
优先使用富途（实时），备用 Yahoo/Alpha Vantage

作者: 虾虾 🦐
"""

try:
    from futu import *
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器 - 优先富途"""

    def __init__(self, alpha_vantage_key: str = "", use_futu: bool = True):
        """
        初始化

        Args:
            alpha_vantage_key: Alpha Vantage API Key
            use_futu: 是否优先使用富途
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.use_futu = use_futu and FUTU_AVAILABLE
        self.quote_ctx = None
        
        # 富途连接
        if self.use_futu:
            try:
                self.quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
                logger.info("富途行情连接成功")
            except Exception as e:
                logger.warning(f"富途连接失败: {e}, 将使用备用数据源")
                self.use_futu = False

    # ==================== 富途行情 ====================
    
    def get_quote_futu(self, symbol: str, market: str = "HK") -> Optional[dict]:
        """获取富途报价"""
        if not self.use_futu or not self.quote_ctx:
            return None
            
        try:
            # 格式化代码
            code = f"{market.upper()}.{symbol}"
            ret, data = self.quote_ctx.get_stock_quote([code])
            if ret == 0 and not data.empty:
                row = data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row.get('name', ''),
                    "price": row.get('last_price', 0),
                    "open": row.get('open_price', 0),
                    "high": row.get('high_price', 0),
                    "low": row.get('low_price', 0),
                    "volume": row.get('volume', 0),
                    "change": row.get('change_val', 0),
                    "change_pct": row.get('change_rate', 0),
                    "bid": row.get('bid_price', 0),
                    "ask": row.get('ask_price', 0),
                    "source": f"Futu {market}"
                }
        except Exception as e:
            logger.error(f"富途获取报价失败: {e}")
        return None

    def get_history_futu(self, symbol: str, market: str = "HK", 
                       start: str = "", end: str = "", days: int = 30) -> pd.DataFrame:
        """获取富途K线"""
        if not self.use_futu or not self.quote_ctx:
            return pd.DataFrame()
            
        try:
            code = f"{market.upper()}.{symbol}"
            ret, data = self.quote_ctx.get_history_kline(
                code, start or "2020-01-01", end or "2026-12-31", 
                KL_TYPE.KL_DAY, ""
            )
            if ret == 0 and not data.empty:
                return data
        except Exception as e:
            logger.error(f"富途获取K线失败: {e}")
        return pd.DataFrame()

    # ==================== Alpha Vantage (美股) ====================

    def get_quote_av(self, symbol: str) -> Optional[dict]:
        """获取美股报价 (Alpha Vantage)"""
        if not self.alpha_vantage_key:
            return None

        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.alpha_vantage_key
        }

        try:
            response = requests.get("https://www.alphavantage.co/query", 
                                  params=params, timeout=10)
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
                "source": "AlphaVantage"
            }
        except Exception as e:
            logger.error(f"Alpha Vantage 获取失败: {e}")
            return None

    # ==================== Yahoo Finance (港股备用) ====================

    def get_quote_yf(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """获取港股报价 (Yahoo)"""
        try:
            ticker = symbol
            if market == "hk" and not symbol.endswith(".HK"):
                ticker = f"{int(symbol):04d}.HK"

            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                "symbol": symbol,
                "price": info.get("currentPrice", info.get("previousClose", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("volume", 0),
                "source": "Yahoo"
            }
        except Exception as e:
            logger.error(f"Yahoo 获取失败: {e}")
            return None

    # ==================== 统一接口 ====================

    def get_quote(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """
        获取报价 (自动选择数据源)
        
        优先级: 富途 > Alpha Vantage > Yahoo
        """
        # 优先富途
        if market.lower() in ["hk", "us"]:
            quote = self.get_quote_futu(symbol, market.upper())
            if quote:
                return quote
        
        # 美股用 Alpha Vantage
        if market.lower() == "us":
            return self.get_quote_av(symbol)
        
        # 港股用 Yahoo
        return self.get_quote_yf(symbol, market)

    def get_history(self, symbol: str, market: str = "hk", 
                   days: int = 30, period: str = None, interval: str = None) -> pd.DataFrame:
        """获取历史K线"""
        # 优先富途
        if self.use_futu and market.lower() in ["hk", "us"]:
            df = self.get_history_futu(symbol, market.upper(), days=days)
            if not df.empty:
                return df
        
        # 备用 Yahoo
        return self.get_history_yf(symbol, period or f"{days}d", interval)

    def get_history_yf(self, symbol: str, period: str = "1mo", interval: str = None) -> pd.DataFrame:
        """Yahoo K线"""
        try:
            ticker = f"{int(symbol):04d}.HK" if symbol.isdigit() else symbol
            stock = yf.Ticker(ticker)
            return stock.history(period=period, interval=interval)
        except Exception as e:
            logger.error(f"Yahoo K线失败: {e}")
            return pd.DataFrame()

    def get_forex(self, from_curr: str = "USD", to_curr: str = "HKD") -> Optional[dict]:
        """获取汇率"""
        try:
            url = f"https://api.frankfurter.app/latest?from={from_curr}&to={to_curr}"
            response = requests.get(url, timeout=10)
            data = response.json()
            rate = data.get("rates", {}).get(to_curr)
            if rate:
                return {"from": from_curr, "to": to_curr, "rate": rate, "source": "Frankfurter"}
        except Exception as e:
            logger.error(f"汇率获取失败: {e}")
        return None

    def get_crypto(self, symbol: str = "BTC") -> Optional[dict]:
        """获取加密货币"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            data = response.json()
            price = data.get(symbol.lower(), {}).get("usd")
            if price:
                return {"symbol": symbol.upper(), "price": price, "source": "CoinGecko"}
        except Exception as e:
            logger.error(f"加密货币获取失败: {e}")
        return None

    def close(self):
        """关闭连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            logger.info("富途连接已关闭")


# ==================== 测试 ====================
if __name__ == "__main__":
    fetcher = DataFetcher()
    
    print("=== 港股行情 ===")
    q = fetcher.get_quote("00700", "hk")
    print(f"腾讯: {q}")
    
    print("\n=== 美股行情 ===")
    q = fetcher.get_quote("AAPL", "us")
    print(f"Apple: {q}")
    
    print("\n=== 汇率 ===")
    r = fetcher.get_forex("USD", "HKD")
    print(f"USD/HKD: {r}")
    
    fetcher.close()
