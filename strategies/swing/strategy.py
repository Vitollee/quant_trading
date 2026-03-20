#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
波段交易策略
功能: 2-5天持仓的波段交易
作者: 虾虾 🦐
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

from data.fetcher import DataFetcher

logger = logging.getLogger(__name__)


class SwingStrategy:
    """波段交易策略"""
    
    def __init__(self, config: dict, fetcher: DataFetcher = None):
        """
        初始化策略

        Args:
            config: 策略配置
            fetcher: 数据获取器（可选）
        """
        self.config = config
        self.fetcher = fetcher or DataFetcher()
        
        # 策略参数
        swing_config = config.get("strategy_swing", {})
        
        # 支撑/阻力位参数
        self.rsi_period = swing_config.get("rsi_period", 14)
        self.rsi_oversold = swing_config.get("rsi_oversold", 35)
        self.rsi_overbought = swing_config.get("rsi_overbought", 65)
        
        # 持仓周期
        self.holding_days = swing_config.get("holding_days", [2, 5])
    
    def analyze(self, symbol: str, market: str = "hk") -> Optional[Dict]:
        """
        分析股票产生波段交易信号

        Args:
            symbol: 股票代码
            market: 市场类型

        Returns:
            dict: 分析结果和信号
        """
        try:
            # 获取数据
            hist = self.fetcher.get_history(symbol, market, days=60)
            if hist.empty or len(hist) < 20:
                return None
            
            close = hist['close'] if 'close' in hist.columns else hist['Close']
            
            # 计算指标
            ma20 = close.rolling(20).mean().iloc[-1]
            ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else close.mean()
            
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
            rs = gain / loss
            rsi = (100 - (100 / (1 + rs))).iloc[-1]
            
            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            
            macd_cross = (macd.iloc[-1] > signal.iloc[-1]) and (macd.iloc[-2] <= signal.iloc[-2])
            
            # 支撑/阻力位
            low_20d = close.rolling(20).min().iloc[-1]
            high_20d = close.rolling(20).max().iloc[-1]
            
            # 布林带
            bb_std = close.rolling(20).std().iloc[-1]
            bb_lower = ma20 - 2 * bb_std
            bb_upper = ma20 + 2 * bb_std
            
            current_price = close.iloc[-1]
            
            # 信号评分
            score = 0
            reasons = []
            
            # 1. 价格在支撑位附近
            support_distance = (current_price - low_20d) / low_20d * 100
            if support_distance < 5:
                score += 25
                reasons.append(f"接近支撑位({support_distance:.1f}%)")
            
            # 2. RSI超卖
            if rsi < self.rsi_oversold:
                score += 25
                reasons.append(f"RSI超卖({rsi:.0f})")
            elif rsi < 45:
                score += 15
                reasons.append(f"RSI偏低({rsi:.0f})")
            
            # 3. MACD金叉
            if macd_cross:
                score += 25
                reasons.append("MACD金叉")
            
            # 4. 价格在布林下轨附近
            bb_distance = (current_price - bb_lower) / bb_lower * 100
            if bb_distance < 3:
                score += 15
                reasons.append(f"触及布林下轨({bb_distance:.1f}%)")
            
            # 5. 站上MA20
            if current_price > ma20:
                score += 10
                reasons.append("站上MA20")
            
            # 生成信号
            if score >= 50:
                signal = "BUY"
                entry = current_price
                stop = low_20d * 0.98  # 止损在支撑下方2%
                target = high_20d  # 目标阻力位
            elif score >= 35:
                signal = "WATCH"
                entry = None
                stop = None
                target = None
            else:
                signal = "HOLD"
                entry = None
                stop = None
                target = None
            
            return {
                "symbol": symbol,
                "market": market,
                "price": current_price,
                "score": score,
                "signal": signal,
                "reason": ", ".join(reasons) if reasons else "无明显信号",
                "entry": entry,
                "stop": stop,
                "target": target,
                "rsi": rsi,
                "ma20": ma20,
                "ma60": ma60,
                "macd_cross": macd_cross,
            }
            
        except Exception as e:
            logger.error(f"波段分析失败 {symbol}: {e}")
            return None
    
    def batch_analyze(self, symbols: list, market: str = "hk") -> list:
        """
        批量分析股票

        Args:
            symbols: 股票代码列表
            market: 市场类型

        Returns:
            list: 分析结果列表
        """
        results = []
        for symbol in symbols:
            result = self.analyze(symbol, market)
            if result:
                results.append(result)
        
        # 按得分排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results
