#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据获取模块 - 富途 + Alpha Vantage + Yahoo Finance
优先使用富途（实时），备用 Yahoo/Alpha Vantage

作者: 虾虾 🦐
"""

try:
    from futu import OpenQuoteContext
    from futu.common.constant import KLType
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    KLType = None

import yfinance as yf
import pandas as pd
import requests
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器 - 优先富途"""

    def __init__(self, alpha_vantage_key: str = "", use_futu: bool = True, finnhub_key: str = ""):
        """
        初始化

        Args:
            alpha_vantage_key: Alpha Vantage API Key
            use_futu: 是否优先使用富途
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.use_futu = use_futu and FUTU_AVAILABLE
        self.finnhub_key = finnhub_key
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
        if not self.use_futu or not self.quote_ctx or KLType is None:
            return pd.DataFrame()
            
        try:
            code = f"{market.upper()}.{symbol}"
            ret, data, page_key = self.quote_ctx.request_history_kline(
                code, start=start or "2020-01-01", end=end or "2026-12-31", 
                ktype=KLType.K_DAY
            )
            if ret == 0 and data is not None and not data.empty:
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

    # ==================== Finnhub (美股) ====================

    def get_quote_finnhub(self, symbol: str) -> Optional[dict]:
        """获取美股报价 (Finnhub)"""
        if not self.finnhub_key:
            return None
            
        try:
            import requests
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
            r = requests.get(url, timeout=10)
            data = r.json()
            
            if data.get("c"):  # c = current price
                return {
                    "symbol": symbol,
                    "price": data.get("c", 0),
                    "change": data.get("d", 0),
                    "change_pct": data.get("dp", 0),
                    "high": data.get("h", 0),
                    "low": data.get("l", 0),
                    "open": data.get("o", 0),
                    "prev_close": data.get("pc", 0),
                    "source": "Finnhub"
                }
        except Exception as e:
            logger.error(f"Finnhub 获取失败: {e}")
        return None

    # ==================== Yahoo Finance (港股备用) ====================

    def get_quote_yf(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """获取港股报价 (Yahoo)"""
        try:
            ticker = symbol
            
            # 港股：转换为 Yahoo 格式
            if market.lower() == "hk":
                if symbol.endswith(".HK"):
                    ticker = symbol
                elif symbol.isdigit():
                    ticker = f"{int(symbol):04d}.HK"
                else:
                    ticker = f"{symbol}.HK"
            # 美股：Yahoo 直接用 symbol
            elif market.lower() == "us":
                ticker = symbol.upper()
            else:
                ticker = symbol

            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or not info.get("regularMarketPrice"):
                # 尝试备用格式
                if market.lower() == "hk" and not symbol.endswith(".HK"):
                    stock = yf.Ticker(f"{symbol}.HK")
                    info = stock.info

            return {
                "symbol": symbol,
                "price": info.get("regularMarketPrice", info.get("currentPrice", info.get("previousClose", 0))),
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
        
        优先级: 富途 > Finnhub > Alpha Vantage > Yahoo
        """
        # 优先富途 (港股)
        if market.lower() == "hk":
            quote = self.get_quote_futu(symbol, market.upper())
            if quote:
                return quote
            return self.get_quote_yf(symbol, market)
        
        # 美股
        if market.lower() == "us":
            # 优先 Finnhub
            quote = self.get_quote_finnhub(symbol)
            if quote:
                return quote
            # 备用 Alpha Vantage
            return self.get_quote_av(symbol)
        
        return None

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

    def get_financials(self, symbol: str, market: str = "hk") -> Optional[dict]:
        """
        获取财务数据 (Yahoo Finance)
        
        Args:
            symbol: 股票代码
            market: 市场类型 (hk/us)
            
        Returns:
            dict: 财务指标数据
        """
        try:
            ticker = symbol
            if market.lower() == "hk":
                if not symbol.endswith(".HK"):
                    ticker = f"{int(symbol):04d}.HK"
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 提取关键财务指标
            financials = {
                "pe_ratio": info.get("trailingPE", info.get("forwardPE", 0)),
                "forward_pe": info.get("forwardPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "ps_ratio": info.get("priceToSalesTrailing12Months", 0),
                "roe": info.get("returnOnEquity", 0),
                "roa": info.get("returnOnAssets", 0),
                "gross_margin": info.get("grossMargins", 0),
                "operating_margin": info.get("operatingMargins", 0),
                "net_margin": info.get("profitMargins", 0),
                "revenue": info.get("totalRevenue", 0),
                "revenue_growth": info.get("revenueGrowth", 0),
                "earnings_growth": info.get("earningsGrowth", 0),
                "eps": info.get("trailingEps", info.get("forwardEps", 0)),
                "eps_growth": info.get("epsGrowth", 0),
                "book_value": info.get("bookValue", 0),
                "total_cash": info.get("totalCash", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "current_ratio": info.get("currentRatio", 0),
                "quick_ratio": info.get("quickRatio", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "market_cap": info.get("marketCap", 0),
                "enterprise_value": info.get("enterpriseValue", 0),
                "source": "Yahoo"
            }
            
            return financials
            
        except Exception as e:
            logger.error(f"获取财务数据失败 {symbol}: {e}")
            return None

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

    def get_technical(self, symbol: str, market: str = "us") -> Dict:
        """
        获取技术指标
        
        Args:
            symbol: 股票代码
            market: 市场类型
            
        Returns:
            dict: 技术指标数据
        """
        try:
            import yfinance as yf
            
            ticker = symbol
            if market == "hk":
                ticker = f"{int(symbol):04d}.HK"
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            if hist.empty:
                return {}
            
            close = hist['Close']
            
            # MA
            ma5 = close.rolling(5).mean().iloc[-1]
            ma10 = close.rolling(10).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
            
            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = (ema12 - ema26).iloc[-1]
            signal = macd.ewm(span=9).mean() if hasattr(macd, 'ewm') else macd
            
            return {
                "symbol": symbol,
                "price": close.iloc[-1],
                "ma5": ma5,
                "ma10": ma10,
                "ma20": ma20,
                "rsi": rsi,
                "macd": macd,
                "volume": hist['Volume'].iloc[-1],
                "source": "Yahoo"
            }
        except Exception as e:
            logger.error(f"技术指标获取失败: {e}")
            return {}

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
