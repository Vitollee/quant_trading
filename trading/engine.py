#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟交易引擎
功能: 执行买卖操作，记录持仓，计算盈亏
作者: 虾虾 🦐
"""

import yaml
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingEngine:
    """模拟交易引擎"""

    def __init__(self, config: dict):
        """
        初始化交易引擎

        Args:
            config: 配置文件
        """
        self.config = config
        self.capital_config = config.get("capital", {})
        self.initial_capital = self.capital_config.get("initial", 100000)
        self.currency = self.capital_config.get("currency", "HKD")

        # 模拟交易配置
        sim_config = config.get("simulation", {})
        self.slippage = sim_config.get("slippage", {})
        self.commission = sim_config.get("commission", {})

        # 持仓和现金
        self.cash = self.initial_capital
        self.positions = {}  # symbol -> {quantity, cost_price, market}

        # 交易记录
        self.trades = []
        self.equity_curve = []

    def buy(self, symbol: str, price: float, quantity: int = 0,
           amount: float = 0, market: str = "hk") -> Dict:
        """
        买入

        Args:
            symbol: 股票代码
            price: 价格
            quantity: 股数 (二选一)
            amount: 金额 (二选一)
            market: 市场

        Returns:
            dict: 交易结果
        """
        # 检查价格
        if not price or price <= 0:
            logger.warning(f"无效价格 {symbol}: {price}")
            return {"success": False, "reason": "invalid_price"}
            
        # 计算实际买入数量
        if amount > 0:
            # 滑点
            slip = self.slippage.get(market, 0.001)
            actual_price = price * (1 + slip)

            # 手续费
            comm = self.commission.get(market, 0.001)
            available = self.cash / (1 + comm)
            quantity = int(available / actual_price)
            total = quantity * actual_price
            fee = total * comm
        else:
            quantity = quantity
            slip = self.slippage.get(market, 0.001)
            actual_price = price * (1 + slip)
            total = quantity * actual_price
            fee = total * self.commission.get(market, 0.001)

        if total + fee > self.cash:
            logger.warning(f"资金不足，无法买入 {symbol}")
            return {"success": False, "reason": "insufficient_cash"}

        # 执行买入
        self.cash -= (total + fee)

        # 更新持仓
        if symbol in self.positions:
            old_qty = self.positions[symbol]["quantity"]
            old_cost = self.positions[symbol]["cost_price"]
            new_qty = old_qty + quantity
            new_cost = (old_qty * old_cost + quantity * actual_price) / new_qty

            self.positions[symbol] = {
                "quantity": new_qty,
                "cost_price": new_cost,
                "market": market
            }
        else:
            self.positions[symbol] = {
                "quantity": quantity,
                "cost_price": actual_price,
                "market": market
            }

        # 记录交易
        trade = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": "BUY",
            "price": actual_price,
            "quantity": quantity,
            "fee": fee,
            "total": total + fee
        }
        self.trades.append(trade)

        logger.info(f"买入 {symbol} x{quantity} @ {actual_price:.2f}")

        return {
            "success": True,
            "trade": trade,
            "cash": self.cash,
            "position": self.positions[symbol]
        }

    def sell(self, symbol: str, price: float, quantity: int = 0,
            market: str = "hk") -> Dict:
        """
        卖出

        Args:
            symbol: 股票代码
            price: 价格
            quantity: 股数 (0表示全部卖出)
            market: 市场

        Returns:
            dict: 交易结果
        """
        if symbol not in self.positions:
            logger.warning(f"没有持仓 {symbol}")
            return {"success": False, "reason": "no_position"}

        pos = self.positions[symbol]
        sell_qty = quantity if quantity > 0 else pos["quantity"]

        # 滑点
        slip = self.slippage.get(market, 0.001)
        actual_price = price * (1 - slip)

        # 手续费
        comm = self.commission.get(market, 0.001)
        total = sell_qty * actual_price
        fee = total * comm

        # 执行卖出
        self.cash += (total - fee)

        # 更新持仓
        if quantity == 0 or quantity >= pos["quantity"]:
            del self.positions[symbol]
        else:
            pos["quantity"] -= quantity

        # 记录交易
        trade = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": "SELL",
            "price": actual_price,
            "quantity": sell_qty,
            "fee": fee,
            "total": total - fee
        }
        self.trades.append(trade)

        # 计算盈亏
        cost = pos["cost_price"] * sell_qty
        pnl = total - fee - cost
        pnl_pct = pnl / cost * 100

        logger.info(f"卖出 {symbol} x{sell_qty} @ {actual_price:.2f}, PnL: {pnl:.2f} ({pnl_pct:.1f}%)")

        return {
            "success": True,
            "trade": trade,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "cash": self.cash,
            "position": self.positions.get(symbol)
        }

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        """
        获取组合市值

        Args:
            current_prices: 当前价格字典

        Returns:
            dict: 组合信息
        """
        position_value = 0
        position_pnl = 0

        for symbol, pos in self.positions.items():
            price = current_prices.get(symbol, pos["cost_price"])
            value = price * pos["quantity"]
            cost = pos["cost_price"] * pos["quantity"]
            pnl = value - cost

            position_value += value
            position_pnl += pnl

        total_value = self.cash + position_value
        total_pnl = position_pnl
        total_pnl_pct = (position_pnl / (total_value - position_pnl) * 100) if total_value > position_pnl else 0

        return {
            "cash": self.cash,
            "position_value": position_value,
            "total_value": total_value,
            "pnl": total_pnl,
            "pnl_pct": total_pnl_pct,
            "positions": self.positions,
            "num_positions": len(self.positions)
        }

    def get_positions_summary(self) -> List[Dict]:
        """
        获取持仓摘要

        Returns:
            list: 持仓列表
        """
        summary = []
        for symbol, pos in self.positions.items():
            summary.append({
                "symbol": symbol,
                "quantity": pos["quantity"],
                "cost_price": pos["cost_price"],
                "market": pos["market"]
            })
        return summary

    def get_trades_summary(self, days: int = 30) -> List[Dict]:
        """
        获取交易记录

        Args:
            days: 最近多少天

        Returns:
            list: 交易记录
        """
        return self.trades[-days:]

    def save_state(self, filepath: str):
        """
        保存状态到文件

        Args:
            filepath: 文件路径
        """
        state = {
            "cash": self.cash,
            "positions": self.positions,
            "trades": self.trades,
            "initial_capital": self.initial_capital,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(filepath, "w") as f:
            json.dump(state, f, indent=2, default=str)

        logger.info(f"状态已保存到 {filepath}")

    def load_state(self, filepath: str):
        """
        从文件加载状态

        Args:
            filepath: 文件路径
        """
        try:
            with open(filepath, "r") as f:
                state = json.load(f)

            self.cash = state.get("cash", self.initial_capital)
            self.positions = state.get("positions", {})
            self.trades = state.get("trades", [])

            logger.info(f"状态已从 {filepath} 加载")
            logger.info(f"现金: {self.cash}, 持仓: {len(self.positions)}")

        except Exception as e:
            logger.error(f"加载状态失败: {e}")


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 创建交易引擎
    config = {
        "capital": {
            "initial": 100000,
            "currency": "HKD"
        },
        "simulation": {
            "slippage": {"hk": 0.001, "us": 0.0005},
            "commission": {"hk": 0.0003, "us": 0.001}
        }
    }

    engine = TradingEngine(config)

    print(f"初始资金: {engine.cash}")

    # 测试买入
    result = engine.buy("00700", 350, amount=10000, market="hk")
    print(f"买入结果: {result['success']}")
    print(f"剩余现金: {engine.cash}")
    print(f"持仓: {engine.positions}")

    # 测试卖出
    result = engine.sell("00700", 360, market="hk")
    print(f"卖出结果: {result['success']}")
    print(f"剩余现金: {engine.cash}")

    # 保存状态
    engine.save_state("/tmp/trading_state.json")
