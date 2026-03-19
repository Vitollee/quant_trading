#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易系统 - 改进版 V2
结合 Vnstock 和 Screeni-py 设计思路

功能:
- 股票数据获取 (Yahoo Finance)
- 技术指标计算
- 形态识别
- 选股筛选
- 信号生成

作者: 虾虾 🦐
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockData:
    """股票数据类 - 类似 Vnstock 设计"""

    def __init__(self, symbol: str, market: str = "hk"):
        """
        初始化

        Args:
            symbol: 股票代码
            market: 市场类型 (hk/us)
        """
        self.symbol = symbol.upper()
        self.market = market
        self.ticker = self._format_symbol()
        self._data = None
        self._info = None

    def _format_symbol(self) -> str:
        """格式化代码"""
        sym = self.symbol
        if self.market == "hk":
            # 港股: 保持4位数字，如 00700 -> 0700.HK
            if sym.isdigit():
                # 去掉前导0但保持4位
                sym = sym.lstrip('0') or '0'
                # 不足4位前面补0
                sym = sym.zfill(4)
            return f"{sym}.HK"
        return sym

    def history(self, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """获取历史K线"""
        try:
            data = yf.download(self.ticker, period=period, interval=interval, progress=False)
            return data
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()

    def info(self) -> Dict:
        """获取股票信息"""
        try:
            if not self._info:
                t = yf.Ticker(self.ticker)
                self._info = t.info
            return self._info
        except Exception as e:
            logger.error(f"获取信息失败: {e}")
            return {}

    def quote(self) -> Dict:
        """获取实时报价"""
        info = self.info()
        return {
            "symbol": self.symbol,
            "price": info.get("currentPrice", 0),
            "change": info.get("regularMarketChange", 0),
            "change_pct": info.get("regularMarketChangePercent", 0),
            "volume": info.get("volume", 0),
            "high52w": info.get("fiftyTwoWeekHigh", 0),
            "low52w": info.get("fiftyTwoWeekLow", 0),
            "pe": info.get("trailingPE", 0),
            "market_cap": info.get("marketCap", 0),
        }

    def financials(self) -> Dict:
        """获取财务数据"""
        info = self.info()
        return {
            "pe": info.get("trailingPE", 0),
            "pb": info.get("priceToBook", 0),
            "roe": info.get("returnOnEquity", 0),
            "gross_margin": info.get("grossMargins", 0),
            "revenue_growth": info.get("revenueGrowth", 0),
            "earnings_growth": info.get("earningsGrowth", 0),
            "debt_to_equity": info.get("debtToEquity", 0),
        }


class TechnicalIndicators:
    """技术指标类 - 类似 Screeni-py 设计"""

    @staticmethod
    def calculate(df: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        df = df.copy()

        # 基础指标
        try:
            df["RSI"] = TechnicalIndicators.rsi(df["Close"])
        except:
            df["RSI"] = 0
            
        try:
            macd, signal, hist = TechnicalIndicators.macd(df["Close"])
            df["MACD"] = macd
            df["Signal"] = signal
            df["Hist"] = hist
        except:
            df["MACD"] = 0
            df["Signal"] = 0
            df["Hist"] = 0
            
        try:
            df["BB_Upper"], df["BB_Middle"], df["BB_Lower"] = TechnicalIndicators.bollinger_bands(df["Close"])
        except:
            df["BB_Upper"] = df["BB_Middle"] = df["BB_Lower"] = 0
            
        df["SMA_20"] = df["Close"].rolling(20).mean()
        df["SMA_50"] = df["Close"].rolling(50).mean()
        df["EMA_12"] = df["Close"].ewm(span=12).mean()
        df["EMA_26"] = df["Close"].ewm(span=26).mean()

        # 趋势指标 (暂时跳过ADX，容易出错)
        # df["ADX"] = TechnicalIndicators.adx(df["High"], df["Low"], df["Close"])
        df["ATR"] = 0

        # 成交量指标
        df["Volume_SMA"] = df["Volume"].rolling(20).mean()

        return df

    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """RSI 相对强弱指标"""
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD 指标"""
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    @staticmethod
    def bollinger_bands(close: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """布林带"""
        middle = close.rolling(period).mean()
        std = close.rolling(period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ADX 趋势指标"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(14).mean()
        return adx

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ATR 真实波动幅度"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()


class PatternRecognition:
    """形态识别 - 类似 Screeni-py 设计"""

    @staticmethod
    def recognize(df: pd.DataFrame, lookback: int = 50) -> Dict[str, bool]:
        """
        识别形态

        Returns:
            dict: 形态识别结果
        """
        if len(df) < lookback:
            return {}

        recent = df.tail(lookback)

        patterns = {}

        # 早晨之星 (Bullish)
        patterns["morning_star"] = bool(PatternRecognition._morning_star(recent))

        # 黄昏之星 (Bearish)
        patterns["evening_star"] = bool(PatternRecognition._evening_star(recent))

        # 吞没形态 (Bullish/Bearish)
        patterns["bullish_engulfing"] = bool(PatternRecognition._bullish_engulfing(recent))
        patterns["bearish_engulfing"] = bool(PatternRecognition._bearish_engulfing(recent))

        # 锤子线 (Bullish)
        patterns["hammer"] = bool(PatternRecognition._hammer(recent))

        # 突破新高
        patterns["breakout_high"] = bool(PatternRecognition._breakout_high(recent))

        # 突破新低
        patterns["breakout_low"] = bool(PatternRecognition._breakout_low(recent))

        return patterns

    @staticmethod
    def _morning_star(df: pd.DataFrame) -> bool:
        """早晨之星 - 底部反转"""
        if len(df) < 3:
            return False
        try:
            closes = df["Close"].iloc[-3:].values
            if len(closes) < 3:
                return False
            c1, c2, c3 = closes
            o1 = df["Open"].iloc[-3]
            # 第一天大跌
            if c1 < o1:
                # 第三天大涨
                if c3 > (o1 + c1) / 2:
                    return True
        except:
            pass
        return False

    @staticmethod
    def _evening_star(df: pd.DataFrame) -> bool:
        """黄昏之星 - 顶部反转"""
        if len(df) < 3:
            return False
        try:
            closes = df["Close"].iloc[-3:].values
            if len(closes) < 3:
                return False
            c1, c2, c3 = closes
            o1 = df["Open"].iloc[-3]
            if c1 > o1:
                if c3 < (o1 + c1) / 2:
                    return True
        except:
            pass
        return False

    @staticmethod
    def _bullish_engulfing(df: pd.DataFrame) -> bool:
        """看涨吞没"""
        if len(df) < 2:
            return False
        try:
            prev = df.iloc[-2]
            curr = df.iloc[-1]
            # 前一天阴线，当天阳线
            if prev["Close"] < prev["Open"] and curr["Close"] > curr["Open"]:
                # 阳线包住阴线
                if curr["Close"] > prev["Open"] and curr["Open"] < prev["Close"]:
                    return True
        except:
            pass
        return False

    @staticmethod
    def _bearish_engulfing(df: pd.DataFrame) -> bool:
        """看跌吞没"""
        if len(df) < 2:
            return False
        try:
            prev = df.iloc[-2]
            curr = df.iloc[-1]
            if prev["Close"] > prev["Open"] and curr["Close"] < curr["Open"]:
                if curr["Open"] > prev["Close"] and curr["Close"] < prev["Open"]:
                    return True
        except:
            pass
        return False

    @staticmethod
    def _hammer(df: pd.DataFrame) -> bool:
        """锤子线 - 底部信号"""
        if len(df) < 1:
            return False
        try:
            candle = df.iloc[-1]
            body = abs(candle["Close"] - candle["Open"])
            lower_shadow = min(candle["Open"], candle["Close"]) - candle["Low"]
            upper_shadow = candle["High"] - max(candle["Open"], candle["Close"])
            if lower_shadow > body * 2 and upper_shadow < body:
                return True
        except:
            pass
        return False

    @staticmethod
    def _breakout_high(df: pd.DataFrame) -> bool:
        """突破20日高点"""
        if len(df) < 20:
            return False
        try:
            current = float(df["Close"].iloc[-1])
            high_20 = float(df["High"].tail(20).max())
            return bool(current > high_20)
        except:
            return False

    @staticmethod
    def _breakout_low(df: pd.DataFrame) -> bool:
        """跌破20日低点"""
        if len(df) < 20:
            return False
        try:
            current = float(df["Close"].iloc[-1])
            low_20 = float(df["Low"].tail(20).min())
            return bool(current < low_20)
        except:
            return False


class StockScreener:
    """股票筛选器 - 结合 Vnstock 和 Screeni-py"""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def screen(
        self,
        symbols: List[str],
        market: str = "hk",
        filters: Dict = None
    ) -> pd.DataFrame:
        """
        筛选股票

        Args:
            symbols: 股票列表
            market: 市场
            filters: 筛选条件

        Returns:
            DataFrame: 筛选结果
        """
        results = []

        for symbol in symbols:
            try:
                stock = StockData(symbol, market)
                df = stock.history(period="3mo")

                if df.empty:
                    continue

                # 计算技术指标
                df = TechnicalIndicators.calculate(df)

                # 形态识别
                patterns = PatternRecognition.recognize(df)

                # 获取最新数据
                latest = df.iloc[-1]
                # 转换为普通 Series（去除多层索引）
                if hasattr(latest, 'to_dict'):
                    latest = pd.Series(latest.to_dict())
                quote = stock.quote()
                financials = stock.financials()

                # 筛选
                if filters and not self._apply_filters(latest, quote, financials, patterns, filters):
                    continue

                # 安全获取最新值
                def get_val(series, key, default=0):
                    val = series.get(key, default)
                    if hasattr(val, 'iloc'):
                        return float(val.iloc[0]) if len(val) > 0 else default
                    return float(val) if val is not None else default
                
                results.append({
                    "symbol": symbol,
                    "name": quote.get("shortName", ""),
                    "price": get_val(latest, "Close", quote.get("price", 0)),
                    "change_pct": quote.get("change_pct", 0),
                    "rsi": get_val(latest, "RSI", 50),
                    "macd_hist": get_val(latest, "Hist", 0),
                    "bb_position": self._bb_position(latest),
                    **patterns,
                    "score": self._calculate_score(latest, patterns)
                })

            except Exception as e:
                logger.error(f"筛选 {symbol} 失败: {e}")
                continue

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("score", ascending=False)

        return df

    def _apply_filters(self, latest: pd.Series, quote: Dict, financials: Dict, patterns: Dict, filters: Dict) -> bool:
        """应用筛选条件"""
        # 安全获取RSI
        rsi_val = latest.get("RSI", 50)
        if hasattr(rsi_val, 'iloc'):
            rsi_val = float(rsi_val.iloc[0]) if len(rsi_val) > 0 else 50
        rsi_val = float(rsi_val) if rsi_val is not None else 50
        
        # RSI 筛选
        if "rsi_min" in filters:
            if rsi_val < filters["rsi_min"]:
                return False
        if "rsi_max" in filters:
            if rsi_val > filters["rsi_max"]:
                return False

        # 成交量筛选
        if "volume_ratio" in filters:
            vol = latest.get("Volume", 0)
            vol_sma = latest.get("Volume_SMA", 1)
            if hasattr(vol, 'iloc'):
                vol = float(vol.iloc[0]) if len(vol) > 0 else 0
            if hasattr(vol_sma, 'iloc'):
                vol_sma = float(vol_sma.iloc[0]) if len(vol_sma) > 0 else 1
            vol = float(vol) if vol is not None else 0
            vol_sma = float(vol_sma) if vol_sma is not None else 1
            
            if vol_sma > 0:
                vol_ratio = vol / vol_sma
                if vol_ratio < filters["volume_ratio"]:
                    return False

        # 市值筛选 (单位: 亿)
        if "market_cap_min" in filters:
            market_cap = quote.get("market_cap", 0)
            if market_cap < filters["market_cap_min"]:
                return False
        if "market_cap_max" in filters:
            market_cap = quote.get("market_cap", float('inf'))
            if market_cap > filters["market_cap_max"]:
                return False

        # 换手率筛选 (%)
        if "min_turnover_rate" in filters:
            turnover_rate = latest.get("turnover_rate", 0)
            if hasattr(turnover_rate, 'iloc'):
                turnover_rate = float(turnover_rate.iloc[0]) if len(turnover_rate) > 0 else 0
            turnover_rate = float(turnover_rate) if turnover_rate is not None else 0
            if turnover_rate < filters["min_turnover_rate"]:
                return False

        return True

    def _bb_position(self, latest: pd.Series) -> float:
        """布林带位置"""
        try:
            # 确保是标量
            def get_scalar(series, key, default=0):
                val = series.get(key, default)
                if hasattr(val, 'iloc'):
                    return float(val.iloc[0]) if len(val) > 0 else default
                return float(val) if val is not None else default
            
            bb_upper = get_scalar(latest, "BB_Upper", 1)
            bb_lower = get_scalar(latest, "BB_Lower", 0)
            close = get_scalar(latest, "Close", 0)

            if bb_upper == bb_lower or bb_upper == 0:
                return 0

            return (close - bb_lower) / (bb_upper - bb_lower)
        except:
            return 0

    def _calculate_score(self, latest: pd.Series, patterns: Dict) -> int:
        """计算得分"""
        score = 0

        # 安全获取RSI
        rsi_val = latest.get("RSI", 50)
        if hasattr(rsi_val, 'iloc'):
            rsi_val = float(rsi_val.iloc[0]) if len(rsi_val) > 0 else 50
        rsi_val = float(rsi_val) if rsi_val is not None else 50

        # RSI 超卖
        if rsi_val < 35:
            score += 3

        # MACD 金叉
        hist_val = latest.get("Hist", 0)
        if hasattr(hist_val, 'iloc'):
            hist_val = float(hist_val.iloc[0]) if len(hist_val) > 0 else 0
        hist_val = float(hist_val) if hist_val is not None else 0
        
        if hist_val > 0:
            score += 2

        # 布林带超卖
        bb_pos = self._bb_position(latest)
        if bb_pos < 0.2:
            score += 2

        # 形态加分
        if patterns.get("morning_star") or patterns.get("bullish_engulfing") or patterns.get("hammer"):
            score += 5

        if patterns.get("breakout_high"):
            score += 3

        return score


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试数据获取
    print("=== 测试股票数据 ===")
    stock = StockData("00700", "hk")
    print(f"腾讯: {stock.quote()}")

    # 测试技术指标
    print("\n=== 测试技术指标 ===")
    df = stock.history(period="3mo")
    df = TechnicalIndicators.calculate(df)
    print(df.tail()[["Close", "RSI", "MACD", "BB_Upper", "BB_Lower"]])

    # 测试形态识别
    print("\n=== 测试形态识别 ===")
    patterns = PatternRecognition.recognize(df)
    print(f"形态: {patterns}")

    # 测试筛选
    print("\n=== 测试筛选 ===")
    screener = StockScreener()
    hk_symbols = ["00700", "09988", "03690", "02318"]
    result = screener.screen(hk_symbols, "hk")
    if not result.empty:
        cols = [c for c in ["symbol", "price", "rsi", "score"] if c in result.columns]
        print(result[cols] if cols else result)
    else:
        print("无筛选结果")
