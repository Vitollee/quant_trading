#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选股列表管理模块
功能: 管理用户的自选股列表，支持分类
作者: 虾虾 🦐
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Stock:
    """股票"""
    symbol: str      # 代码，如 "00700"
    market: str      # "hk" 或 "us"
    name: str = ""   # 名称，如 "腾讯"
    category: str = "default"  # 分类
    enabled: bool = True       # 是否启用
    notes: str = ""            # 备注


class Watchlist:
    """选股列表管理器"""
    
    DEFAULT_WATCHLIST = {
        "hk": {
            "name": "港股自选",
            "stocks": [
                {"symbol": "00700", "market": "hk", "name": "腾讯", "category": "tech"},
                {"symbol": "09988", "market": "hk", "name": "阿里巴巴", "category": "tech"},
                {"symbol": "03690", "market": "hk", "name": "美团", "category": "tech"},
            ]
        },
        "us": {
            "name": "美股自选",
            "stocks": [
                {"symbol": "NVDA", "market": "us", "name": "英伟达", "category": "tech"},
                {"symbol": "TSLA", "market": "us", "name": "特斯拉", "category": "ev"},
                {"symbol": "AAPL", "market": "us", "name": "苹果", "category": "tech"},
            ]
        }
    }
    
    def __init__(self, config_file: str = "config/watchlist.json"):
        self.config_file = config_file
        self.watchlist = self._load()
    
    def _load(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载选股列表失败: {e}")
        return self.DEFAULT_WATCHLIST.copy()
    
    def _save(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.watchlist, f, ensure_ascii=False, indent=2)
    
    def get_all_stocks(self) -> List[Stock]:
        """获取所有股票"""
        stocks = []
        for market_key, market_data in self.watchlist.items():
            for s in market_data.get("stocks", []):
                stocks.append(Stock(
                    symbol=s["symbol"],
                    market=s["market"],
                    name=s.get("name", ""),
                    category=s.get("category", "default"),
                    enabled=s.get("enabled", True)
                ))
        return stocks
    
    def get_enabled_stocks(self) -> List[Stock]:
        """获取启用的股票"""
        return [s for s in self.get_all_stocks() if s.enabled]
    
    def get_stocks_by_market(self, market: str) -> List[Stock]:
        """按市场获取股票"""
        return [s for s in self.get_all_stocks() if s.market == market and s.enabled]
    
    def get_stocks_by_category(self, category: str) -> List[Stock]:
        """按分类获取股票"""
        return [s for s in self.get_all_stocks() if s.category == category and s.enabled]
    
    def add_stock(self, symbol: str, market: str, name: str = "", category: str = "default"):
        """添加股票"""
        if market not in self.watchlist:
            self.watchlist[market] = {"name": f"{market.upper()} 自选", "stocks": []}
        
        # 检查是否已存在
        for s in self.watchlist[market].get("stocks", []):
            if s["symbol"] == symbol:
                logger.info(f"{symbol} 已存在")
                return
        
        self.watchlist[market]["stocks"].append({
            "symbol": symbol,
            "market": market,
            "name": name,
            "category": category,
            "enabled": True
        })
        self._save()
        logger.info(f"已添加 {symbol} 到 {market} 自选")
    
    def remove_stock(self, symbol: str, market: str):
        """移除股票"""
        if market in self.watchlist:
            self.watchlist[market]["stocks"] = [
                s for s in self.watchlist[market].get("stocks", [])
                if s["symbol"] != symbol
            ]
            self._save()
            logger.info(f"已移除 {symbol} 从 {market}")
    
    def toggle_stock(self, symbol: str, market: str, enabled: bool):
        """启用/禁用股票"""
        if market in self.watchlist:
            for s in self.watchlist[market].get("stocks", []):
                if s["symbol"] == symbol:
                    s["enabled"] = enabled
            self._save()
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        categories = set()
        for s in self.get_all_stocks():
            categories.add(s.category)
        return sorted(list(categories))
    
    def print_watchlist(self):
        """打印选股列表"""
        print("=" * 50)
        print("选股列表")
        print("=" * 50)
        
        for market_key, market_data in self.watchlist.items():
            print(f"\n【{market_data['name']}】")
            for s in market_data.get("stocks", []):
                status = "✓" if s.get("enabled", True) else "✗"
                name = s.get("name", "")
                cat = s.get("category", "")
                print(f"  {status} {s['symbol']} {name} ({cat})")


def edit_watchlist_interactive():
    """交互式编辑选股列表"""
    watchlist = Watchlist()
    
    while True:
        print("\n" + "=" * 50)
        print("选股列表管理")
        print("=" * 50)
        print("1. 查看当前列表")
        print("2. 添加股票")
        print("3. 移除股票")
        print("4. 启用/禁用股票")
        print("5. 保存并退出")
        print("0. 退出（不保存）")
        
        choice = input("\n选择: ").strip()
        
        if choice == "1":
            watchlist.print_watchlist()
        
        elif choice == "2":
            symbol = input("股票代码: ").strip().upper()
            market = input("市场 (hk/us): ").strip().lower()
            name = input("名称 (可选): ").strip()
            category = input("分类 (可选): ").strip() or "default"
            watchlist.add_stock(symbol, market, name, category)
        
        elif choice == "3":
            symbol = input("股票代码: ").strip().upper()
            market = input("市场 (hk/us): ").strip().lower()
            watchlist.remove_stock(symbol, market)
        
        elif choice == "4":
            symbol = input("股票代码: ").strip().upper()
            market = input("市场 (hk/us): ").strip().lower()
            enabled = input("启用? (y/n): ").strip().lower() == "y"
            watchlist.toggle_stock(symbol, market, enabled)
        
        elif choice == "5":
            watchlist._save()
            print("已保存！")
            break
        
        elif choice == "0":
            print("已退出")
            break


if __name__ == "__main__":
    edit_watchlist_interactive()
