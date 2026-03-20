#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易系统 V3
====================
结构:
  setup/     - API配置和选股列表
  data/      - 数据获取层
  strategies/ - 交易策略（long_term/swing/intraday）
  portfolio/ - 持仓管理
  visualization/ - 监控面板

作者: 虾虾 🦐
"""

import yaml
import argparse
import logging
from datetime import datetime

from setup.api_config import APIConfig, setup_api_config
from setup.watchlist import Watchlist
from data.fetcher import DataFetcher
from strategies.long_term.strategy import LongTermStrategy
from strategies.swing.strategy import SwingStrategy
from strategies.intraday.strategy import IntradayStrategy
from portfolio.manager import PortfolioManager
from visualization.dashboard import Dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class QuantTradingSystem:
    """量化交易系统"""

    def __init__(self, config_path: str = "config/config_v2.yaml"):
        """
        初始化系统

        Args:
            config_path: 配置文件路径
        """
        self.start_time = datetime.now()
        
        # 加载配置
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        logger.info("=" * 50)
        logger.info("量化交易系统 V3 启动")
        logger.info("=" * 50)

        # ========== Setup ==========
        self.api_config = APIConfig()
        self.watchlist = Watchlist()
        
        # 检查API配置
        if not self.api_config.is_configured():
            logger.warning("API未配置，请先运行 setup/api_config.py")
        
        # ========== Data Layer ==========
        self.data_fetcher = DataFetcher(self.api_config)
        
        # ========== Strategies ==========
        if self.config.get("strategy_long_term", {}).get("enabled"):
            self.long_term_strategy = LongTermStrategy(self.config)
            logger.info("长期策略已加载")
        
        if self.config.get("strategy_swing", {}).get("enabled"):
            self.swing_strategy = SwingStrategy(self.config)
            logger.info("波段策略已加载")
        
        if self.config.get("strategy_intraday", {}).get("enabled"):
            self.intraday_strategy = IntradayStrategy(self.config)
            logger.info("日内策略已加载")
        
        # ========== Portfolio ==========
        self.portfolio = PortfolioManager()
        
        # ========== Visualization ==========
        self.dashboard = Dashboard()
    
    def run_setup(self):
        """运行设置向导"""
        logger.info("=" * 50)
        logger.info("系统设置")
        logger.info("=" * 50)
        
        # API配置
        print("\n1. API配置")
        setup_api_config()
        
        # 选股列表
        print("\n2. 选股列表")
        from setup.watchlist import edit_watchlist_interactive
        edit_watchlist_interactive()
    
    def run_long_term(self):
        """运行长期策略扫描"""
        if not hasattr(self, 'long_term_strategy'):
            logger.warning("长期策略未启用")
            return
        
        logger.info("=" * 50)
        logger.info("长期策略扫描")
        logger.info("=" * 50)
        
        stocks = self.watchlist.get_stocks_by_market("hk") + \
                 self.watchlist.get_stocks_by_market("us")
        
        for stock in stocks:
            if not stock.enabled:
                continue
            
            result = self.long_term_strategy.analyze(stock.symbol, stock.market)
            if result and result.get("signal") == "BUY":
                logger.info(f"长期买入信号: {stock.symbol} 得分: {result.get('score')}")
    
    def run_swing(self):
        """运行波段策略扫描"""
        if not hasattr(self, 'swing_strategy'):
            logger.warning("波段策略未启用")
            return
        
        logger.info("=" * 50)
        logger.info("波段策略扫描")
        logger.info("=" * 50)
        
        stocks = self.watchlist.get_stocks_by_market("hk") + \
                 self.watchlist.get_stocks_by_market("us")
        
        signals = []
        for stock in stocks:
            if not stock.enabled:
                continue
            
            result = self.swing_strategy.analyze(stock.symbol, stock.market)
            if result and result.get("signal") == "BUY":
                signals.append({
                    "symbol": stock.symbol,
                    "market": stock.market,
                    "score": result.get("score", 0),
                    "price": result.get("price", 0),
                    "reason": result.get("reason", "")
                })
        
        # 按得分排序
        signals.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"\n买入信号 ({len(signals)}个):")
        for s in signals[:10]:
            logger.info(f"  {s['symbol']} {s['market'].upper()} ${s['price']:.2f} 得分:{s['score']:.1f}")
        
        return signals
    
    def run_intraday(self):
        """运行日内策略扫描"""
        if not hasattr(self, 'intraday_strategy'):
            logger.warning("日内策略未启用")
            return
        
        logger.info("=" * 50)
        logger.info("日内策略扫描")
        logger.info("=" * 50)
        
        stocks = self.watchlist.get_stocks_by_market("hk") + \
                 self.watchlist.get_stocks_by_market("us")
        
        signals = []
        for stock in stocks:
            if not stock.enabled:
                continue
            
            result = self.intraday_strategy.analyze(stock.symbol, stock.market)
            if result and result.get("signal") == "BUY":
                signals.append({
                    "symbol": stock.symbol,
                    "market": stock.market,
                    "price": result.get("price", 0),
                    "entry": result.get("entry", 0),
                    "stop": result.get("stop", 0),
                    "target": result.get("target", 0),
                })
        
        logger.info(f"\n日内买入信号 ({len(signals)}个):")
        for s in signals:
            logger.info(f"  {s['symbol']} ${s['price']:.2f} 入:{s['entry']} 止:{s['stop']} 目:{s['target']}")
        
        return signals
    
    def run_dashboard(self):
        """运行监控面板"""
        logger.info("=" * 50)
        logger.info("监控面板")
        logger.info("=" * 50)
        
        # 获取所有信号
        swing_signals = self.run_swing() or []
        intraday_signals = self.run_intraday() or []
        
        # 获取持仓状态
        portfolio = self.portfolio.get_status()
        
        # 生成报告
        self.dashboard.generate_report(
            swing_signals=swing_signals,
            intraday_signals=intraday_signals,
            portfolio=portfolio
        )
    
    def save_state(self):
        """保存状态"""
        import os
        import tempfile
        state_file = os.path.join(tempfile.gettempdir(), "quant_trading_state.json")
        self.portfolio.save_state(state_file)
        logger.info("状态已保存")


def main():
    parser = argparse.ArgumentParser(description="量化交易系统 V3")
    parser.add_argument("--mode", "-m", default="all", 
                       choices=["all", "setup", "long", "swing", "intraday", "dashboard"],
                       help="运行模式")
    parser.add_argument("--config", "-c", default="config/config_v2.yaml",
                       help="配置文件路径")
    
    args = parser.parse_args()
    
    # 初始化系统
    system = QuantTradingSystem(args.config)
    
    # 运行对应模式
    if args.mode == "setup":
        system.run_setup()
    elif args.mode == "long":
        system.run_long_term()
    elif args.mode == "swing":
        system.run_swing()
    elif args.mode == "intraday":
        system.run_intraday()
    elif args.mode == "dashboard":
        system.run_dashboard()
    else:  # all
        system.run_swing()
        system.run_intraday()
        system.run_dashboard()
        system.save_state()
    
    logger.info(f"\n运行时间: {(datetime.now() - system.start_time).total_seconds():.2f}秒")


if __name__ == "__main__":
    main()
