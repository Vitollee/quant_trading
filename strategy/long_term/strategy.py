#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
长周期价值动量策略
功能: 基于估值、成长、质量、动量因子的选股策略
作者: 虾虾 🦐
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import logging

from data.fetcher import DataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LongTermStrategy:
    """长周期价值动量策略"""

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
        strategy_config = config.get("strategy_long_term", config)
        
        # 提取因子权重
        self.factors = strategy_config.get("factors", {})
        self.valuation_weight = self.factors.get("valuation", {}).get("weight", 0.25)
        self.growth_weight = self.factors.get("growth", {}).get("weight", 0.30)
        self.quality_weight = self.factors.get("quality", {}).get("weight", 0.25)
        self.momentum_weight = self.factors.get("momentum", {}).get("weight", 0.20)

        # 持仓配置
        self.position_config = strategy_config.get("position", {})
        self.max_stocks = self.position_config.get("max_stocks", 15)
        self.max_single = self.position_config.get("max_single", 0.10)

        # 风控配置
        self.risk_config = strategy_config.get("risk", {})
        self.stop_loss = self.risk_config.get("stop_loss", -0.08)
        self.take_profit = self.risk_config.get("take_profit", 0.25)

    def scan(self, symbols: List[str], market: str = "hk") -> pd.DataFrame:
        """
        扫描所有股票，计算因子得分

        Args:
            symbols: 股票代码列表
            market: 市场类型

        Returns:
            DataFrame: 包含得分和排名的数据
        """
        results = []

        logger.info(f"开始扫描 {len(symbols)} 只股票...")

        for symbol in symbols:
            try:
                # 获取行情数据
                quote = self.fetcher.get_quote(symbol, market)
                if not quote:
                    continue

                # 获取财务数据
                financials = self.fetcher.get_financials(symbol, market)

                # 计算各因子得分
                scores = self._calculate_scores(quote, financials, market)

                if scores:
                    scores["symbol"] = symbol
                    scores["market"] = market
                    results.append(scores)

            except Exception as e:
                logger.error(f"处理 {symbol} 时出错: {e}")
                continue

        if not results:
            logger.warning("没有找到符合条件的股票")
            return pd.DataFrame()

        # 转换为DataFrame并排序
        df = pd.DataFrame(results)
        df = df.sort_values("total_score", ascending=False)

        logger.info(f"扫描完成，选出 {len(df)} 只股票")

        return df

    def _calculate_scores(self, quote: dict, financials: Optional[dict],
                        market: str) -> Optional[dict]:
        """
        计算单只股票的因子得分

        Args:
            quote: 行情数据
            financials: 财务数据
            market: 市场类型

        Returns:
            dict: 各因子得分
        """
        if not financials:
            # 如果没有财务数据，只用价格动量
            return self._calculate_momentum_only(quote, market)

        # 1. 估值因子得分 (越低越好)
        valuation_score = self._score_valuation(financials)

        # 2. 成长因子得分 (越高越好)
        growth_score = self._score_growth(financials)

        # 3. 质量因子得分 (越高越好)
        quality_score = self._score_quality(financials)

        # 4. 动量因子得分 (近期涨幅越好)
        momentum_score = self._score_momentum(quote)

        # 计算总分
        total_score = (
            valuation_score * self.valuation_weight +
            growth_score * self.growth_weight +
            quality_score * self.quality_weight +
            momentum_score * self.momentum_weight
        )

        return {
            "name": quote.get("name", "N/A"),
            "price": quote.get("price", 0),
            "change_pct": quote.get("change_pct", 0),
            "pe": financials.get("pe_ratio", 0),
            "roe": financials.get("roe", 0),
            "revenue_growth": financials.get("revenue_growth", 0),
            "valuation_score": valuation_score,
            "growth_score": growth_score,
            "quality_score": quality_score,
            "momentum_score": momentum_score,
            "total_score": total_score,
        }

    def _calculate_momentum_only(self, quote: dict, market: str) -> Optional[dict]:
        """只用动量因子（没有财务数据时）"""
        momentum_score = self._score_momentum(quote)

        return {
            "name": quote.get("name", "N/A"),
            "price": quote.get("price", 0),
            "change_pct": quote.get("change_pct", 0),
            "pe": 0,
            "roe": 0,
            "revenue_growth": 0,
            "valuation_score": 0,
            "growth_score": 0,
            "quality_score": 0,
            "momentum_score": momentum_score,
            "total_score": momentum_score,
        }

    def _score_valuation(self, financials: dict) -> float:
        """
        估值因子得分 (0-100, 越低PE/PB越好)

        PE 0-10: 100分
        PE 10-20: 80分
        PE 20-30: 60分
        PE 30-50: 40分
        PE >50: 20分
        """
        pe = financials.get("pe_ratio", 0)
        try:
            pe = float(pe) if pe else 0
        except:
            pe = 0
        if not pe or pe <= 0:
            return 50  # 无数据给中间分

        if pe <= 10:
            return 100
        elif pe <= 20:
            return 80
        elif pe <= 30:
            return 60
        elif pe <= 50:
            return 40
        else:
            return 20

    def _score_growth(self, financials: dict) -> float:
        """
        成长因子得分 (0-100)

        营收增长 > 30%: 100分
        营收增长 20-30%: 80分
        营收增长 10-20%: 60分
        营收增长 0-10%: 40分
        营收增长 < 0%: 20分
        """
        growth = financials.get("revenue_growth", 0)
        if not growth or growth <= 0:
            return 20

        if growth >= 30:
            return 100
        elif growth >= 20:
            return 80
        elif growth >= 10:
            return 60
        elif growth >= 5:
            return 40
        else:
            return 20

    def _score_quality(self, financials: dict) -> float:
        """
        质量因子得分 (0-100)

        ROE > 20%: 100分
        ROE 15-20%: 80分
        ROE 10-15%: 60分
        ROE 5-10%: 40分
        ROE < 5%: 20分
        """
        roe = financials.get("roe", 0)
        if not roe or roe <= 0:
            return 50

        if roe >= 0.20:
            return 100
        elif roe >= 0.15:
            return 80
        elif roe >= 0.10:
            return 60
        elif roe >= 0.05:
            return 40
        else:
            return 20

    def _score_momentum(self, quote: dict) -> float:
        """
        动量因子得分 (0-100)

        近期涨幅越高越好
        """
        change = quote.get("change_pct", 0)

        # 近1日涨跌幅作为动量代理
        if change >= 10:
            return 100
        elif change >= 5:
            return 80
        elif change >= 0:
            return 60
        elif change >= -5:
            return 40
        else:
            return 20

    def generate_signals(self, df: pd.DataFrame) -> List[Dict]:
        """
        根据得分生成交易信号

        Args:
            df: 股票得分表

        Returns:
            List[Dict]: 买入信号列表
        """
        if df.empty:
            return []

        # 取前N只
        top_stocks = df.head(self.max_stocks)

        signals = []
        for _, row in top_stocks.iterrows():
            signal = {
                "symbol": row["symbol"],
                "name": row["name"],
                "price": row["price"],
                "score": row["total_score"],
                "action": "BUY",
                "reason": f"综合得分 {row['total_score']:.1f}, PE={row['pe']:.1f}, 增长={row['revenue_growth']*100:.1f}%"
            }
            signals.append(signal)

        logger.info(f"生成 {len(signals)} 个买入信号")
        return signals

    def check_positions(self, positions: List[Dict], current_prices: Dict) -> List[Dict]:
        """
        检查现有持仓是否需要卖出

        Args:
            positions: 持仓列表
            current_prices: 当前价格字典

        Returns:
            List[Dict]: 卖出信号列表
        """
        sell_signals = []

        for pos in positions:
            symbol = pos.get("symbol")
            cost = pos.get("cost_price", 0)
            current = current_prices.get(symbol, 0)

            if current == 0:
                continue

            # 计算盈亏比例
            pnl_pct = (current - cost) / cost

            # 止损
            if pnl_pct <= self.stop_loss:
                sell_signals.append({
                    "symbol": symbol,
                    "action": "SELL",
                    "reason": f"止损 {pnl_pct*100:.1f}%"
                })
            # 止盈
            elif pnl_pct >= self.take_profit:
                sell_signals.append({
                    "symbol": symbol,
                    "action": "SELL",
                    "reason": f"止盈 {pnl_pct*100:.1f}%"
                })

        return sell_signals


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 模拟配置
    config = {
        "factors": {
            "valuation": {"weight": 0.25},
            "growth": {"weight": 0.30},
            "quality": {"weight": 0.25},
            "momentum": {"weight": 0.20}
        },
        "position": {
            "max_stocks": 15,
            "max_single": 0.10
        },
        "risk": {
            "stop_loss": -0.08,
            "take_profit": 0.25
        }
    }

    strategy = LongTermStrategy(config)

    # 测试港股扫描
    hk_symbols = ["00700", "09988", "03690", "02318", "00939"]
    print("=== 港股扫描测试 ===")
    df = strategy.scan(hk_symbols, "hk")
    if not df.empty:
        print(df[["symbol", "name", "price", "total_score"]].head())

    # 生成信号
    print("\n=== 买入信号 ===")
    signals = strategy.generate_signals(df)
    for s in signals:
        print(f"买入 {s['symbol']} {s['name']} 价格:{s['price']} 得分:{s['score']:.1f}")
