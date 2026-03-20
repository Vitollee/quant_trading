#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓管理模块
功能: 管理持仓、记录交易、计算盈亏
作者: 虾虾 🦐
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Position:
    """持仓"""
    def __init__(self, symbol: str, market: str, quantity: float, avg_cost: float):
        self.symbol = symbol
        self.market = market
        self.quantity = quantity
        self.avg_cost = avg_cost
        self.open_date = datetime.now()


class PortfolioManager:
    """持仓管理器"""
    
    def __init__(self, portfolio_file: str = "portfolio/positions.json"):
        self.portfolio_file = portfolio_file
        self.positions = self._load()
    
    def _load(self) -> List[Dict]:
        """加载持仓"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载持仓失败: {e}")
        return []
    
    def _save(self):
        """保存持仓"""
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        with open(self.portfolio_file, "w", encoding="utf-8") as f:
            json.dump(self.positions, f, ensure_ascii=False, indent=2)
    
    def add_position(self, symbol: str, market: str, quantity: float, avg_cost: float):
        """添加持仓"""
        # 检查是否已存在
        for pos in self.positions:
            if pos["symbol"] == symbol and pos["market"] == market:
                # 更新持仓
                old_qty = pos["quantity"]
                old_cost = pos["avg_cost"]
                new_qty = old_qty + quantity
                new_cost = (old_qty * old_cost + quantity * avg_cost) / new_qty
                pos["quantity"] = new_qty
                pos["avg_cost"] = new_cost
                self._save()
                logger.info(f"更新持仓: {symbol} 数量:{new_qty} 成本:${new_cost:.2f}")
                return
        
        # 新增
        self.positions.append({
            "symbol": symbol,
            "market": market,
            "quantity": quantity,
            "avg_cost": avg_cost,
            "open_date": datetime.now().isoformat()
        })
        self._save()
        logger.info(f"新增持仓: {symbol} 数量:{quantity} 成本:${avg_cost:.2f}")
    
    def remove_position(self, symbol: str, market: str, quantity: float = None):
        """移除持仓"""
        for i, pos in enumerate(self.positions):
            if pos["symbol"] == symbol and pos["market"] == market:
                if quantity is None or quantity >= pos["quantity"]:
                    self.positions.pop(i)
                else:
                    self.positions[i]["quantity"] -= quantity
                self._save()
                logger.info(f"平仓: {symbol}")
                return
    
    def get_position(self, symbol: str, market: str) -> Optional[Dict]:
        """获取持仓"""
        for pos in self.positions:
            if pos["symbol"] == symbol and pos["market"] == market:
                return pos
        return None
    
    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓"""
        return self.positions
    
    def get_status(self) -> Dict:
        """获取账户状态"""
        total_value = 0
        total_cost = 0
        
        for pos in self.positions:
            # 这里需要调用data_fetcher获取实时价格
            # 暂时用成本计算
            cost = pos["quantity"] * pos["avg_cost"]
            total_cost += cost
        
        return {
            "total_cost": total_cost,
            "positions_count": len(self.positions)
        }
    
    def save_state(self, filepath: str):
        """保存状态"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({
                "positions": self.positions,
                "saved_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
