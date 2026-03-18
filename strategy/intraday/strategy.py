#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日内交易策略
功能: 基于RSI、MACD、布林带的短线交易策略
作者: 虾虾 🦐
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, time
import logging

from data.fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntradayStrategy:
    """日内交易策略"""

    def __init__(self, config: dict):
        """
        初始化策略

        Args:
            config: 策略配置字典
        """
        self.config = config
        # 从配置获取 API Key
        av_key = config.get("data_sources", {}).get("quotes", {}).get("alpha_vantage", {}).get("api_key", "")
        self.fetcher = DataFetcher(av_key)

        # 获取策略配置
        strategy_config = config.get("strategy_intraday", config)
        
        # 技术指标参数
        indicators = strategy_config.get("indicators", {})

        # RSI参数
        rsi_config = indicators.get("rsj", {})
        self.rsi_period = rsi_config.get("period", 14)
        self.rsi_oversold = rsi_config.get("oversold", 35)
        self.rsi_overbought = rsi_config.get("overbought", 65)

        # MACD参数
        macd_config = indicators.get("macd", {})
        self.macd_fast = macd_config.get("fast", 12)
        self.macd_slow = macd_config.get("slow", 26)
        self.macd_signal = macd_config.get("signal", 9)

        # 布林带参数
        bb_config = indicators.get("bollinger", {})
        self.bb_period = bb_config.get("period", 20)
        self.bb_std = bb_config.get("std", 2)

        # 持仓配置
        position_config = strategy_config.get("position", {})
        self.max_stocks = position_config.get("max_stocks", 5)
        self.max_single = position_config.get("max_single", 0.20)

        # 风控
        risk_config = strategy_config.get("risk", {})
        self.stop_loss = risk_config.get("stop_loss", -0.03)
        self.take_profit = risk_config.get("take_profit", 0.05)

    def analyze(self, symbol: str, market: str = "hk") -> Dict:
        """
        分析单只股票，产生日内信号

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            dict: 分析结果和信号
        """
        # 获取5分钟和15分钟K线
        df_5m = self.fetcher.get_history(symbol, market, period="1d", interval="5m")
        df_15m = self.fetcher.get_history(symbol, market, period="5d", interval="15m")

        if df_5m.empty:
            logger.warning(f"无数据: {symbol}")
            return {}

        # 计算技术指标
        df_5m = self._calculate_indicators(df_5m)

        # 获取最新数据
        latest = df_5m.iloc[-1]

        # 生成信号
        signals = self._generate_signals(df_5m)

        # 计算得分
        score = self._calculate_signal_score(signals)

        result = {
            "symbol": symbol,
            "market": market,
            "price": latest.get("Close", 0),
            "time": str(latest.name),
            "signals": signals,
            "score": score,
            "action": self._decide_action(score, signals)
        }

        return result

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            df: K线数据

        Returns:
            DataFrame: 包含技术指标的数据
        """
        close = df["Close"]

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        rs = avg_gain / avg_loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = close.ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = close.ewm(span=self.macd_slow, adjust=False).mean()
        df["MACD"] = exp1 - exp2
        df["Signal"] = df["MACD"].ewm(span=self.macd_signal, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["Signal"]

        # 布林带
        df["BB_Middle"] = close.rolling(window=self.bb_period).mean()
        std = close.rolling(window=self.bb_period).std()
        df["BB_Upper"] = df["BB_Middle"] + (std * self.bb_std)
        df["BB_Lower"] = df["BB_Middle"] - (std * self.bb_std)

        # 成交量均线
        df["Vol_MA"] = df["Volume"].rolling(window=5).mean()

        return df

    def _generate_signals(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        生成交易信号

        Args:
            df: 包含技术指标的数据

        Returns:
            dict: 各信号的真值
        """
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        signals = {}

        # RSI信号
        signals["rsi_oversold"] = latest["RSI"] < self.rsi_oversold
        signals["rsi_overbought"] = latest["RSI"] > self.rsi_overbought

        # MACD信号
        signals["macd_golden_cross"] = (
            (prev["MACD"] < prev["Signal"]) and
            (latest["MACD"] > latest["Signal"])
        )
        signals["macd_dead_cross"] = (
            (prev["MACD"] > prev["Signal"]) and
            (latest["MACD"] < latest["Signal"])
        )

        # 布林带信号
        price = latest["Close"]
        signals["bb_lower_touch"] = price <= latest["BB_Lower"]
        signals["bb_upper_touch"] = price >= latest["BB_Upper"]

        # 成交量信号
        signals["volume_surge"] = latest["Volume"] > (latest["Vol_MA"] * 2)

        # 突破信号
        high_20 = df["High"].tail(20).max()
        low_20 = df["Low"].tail(20).min()
        signals["break_high"] = price > high_20
        signals["break_low"] = price < low_20

        return signals

    def _calculate_signal_score(self, signals: Dict[str, bool]) -> int:
        """
        计算信号得分

        Args:
            signals: 信号字典

        Returns:
            int: 信号得分 (买入信号数量)
        """
        # 买入信号
        buy_signals = [
            signals.get("rsi_oversold", False),
            signals.get("macd_golden_cross", False),
            signals.get("bb_lower_touch", False),
            signals.get("volume_surge", False),
            signals.get("break_high", False)
        ]

        return sum(buy_signals)

    def _decide_action(self, score: int, signals: Dict[str, bool]) -> str:
        """
        决定操作

        Args:
            score: 信号得分
            signals: 信号字典

        Returns:
            str: BUY, SELL, 或 HOLD
        """
        # 卖出信号
        if signals.get("rsi_overbought", False):
            return "SELL"
        if signals.get("macd_dead_cross", False):
            return "SELL"
        if signals.get("bb_upper_touch", False):
            return "SELL"
        if signals.get("break_low", False):
            return "SELL"

        # 买入信号 (满足2个以上)
        if score >= 2:
            return "BUY"

        return "HOLD"

    def scan(self, symbols: List[str], market: str = "hk") -> pd.DataFrame:
        """
        批量扫描股票

        Args:
            symbols: 股票列表
            market: 市场类型

        Returns:
            DataFrame: 符合买入条件的股票
        """
        results = []

        logger.info(f"开始日内扫描 {len(symbols)} 只股票...")

        for symbol in symbols:
            try:
                result = self.analyze(symbol, market)
                if result and result.get("action") in ["BUY", "SELL"]:
                    results.append(result)
            except Exception as e:
                logger.error(f"处理 {symbol} 时出错: {e}")
                continue

        if not results:
            logger.info("没有找到符合日内交易条件的股票")
            return pd.DataFrame()

        df = pd.DataFrame(results)
        df = df.sort_values("score", ascending=False)

        logger.info(f"扫描完成，找到 {len(df)} 只股票")
        return df

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        生成交易信号

        Args:
            df: 扫描结果

        Returns:
            List[Dict]: 信号列表
        """
        if df.empty:
            return []

        signals = []

        # 取得分最高的N只
        top = df[df["action"] == "BUY"].head(self.max_stocks)

        for _, row in top.iterrows():
            signal = {
                "symbol": row["symbol"],
                "name": row.get("name", row["symbol"]),
                "price": row["price"],
                "score": row["score"],
                "action": "BUY",
                "reason": f"信号得分 {row['score']}, RSI={row.get('signals',{}).get('rsi_oversold',False)}"
            }
            signals.append(signal)

        return signals

    def check_time_exit(self) -> bool:
        """
        检查是否需要收盘前强制平仓

        Returns:
            bool: 是否需要强平
        """
        now = datetime.now().time()
        exit_time = time(15, 55)  # 15:55

        return now >= exit_time


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 模拟配置
    config = {
        "indicators": {
            "rsi": {"period": 14, "oversold": 35, "overbought": 65},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
            "bollinger": {"period": 20, "std": 2}
        },
        "position": {
            "max_stocks": 5,
            "max_single": 0.20
        },
        "risk": {
            "stop_loss": -0.03,
            "take_profit": 0.05
        }
    }

    strategy = IntradayStrategy(config)

    # 测试
    symbols = ["00700", "09988", "03690"]
    print("=== 日内扫描测试 ===")
    df = strategy.scan(symbols, "hk")
    if not df.empty:
        print(df[["symbol", "price", "score", "action"]])

    print("\n=== 买入信号 ===")
    signals = strategy.generate_signals(df)
    for s in signals:
        print(f"买入 {s['symbol']} 价格:{s['price']} 得分:{s['score']}")
