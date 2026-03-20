#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易系统主入口
功能: 整合数据、策略、交易、监控
作者: 虾虾 🦐
"""

import yaml
import argparse
import logging
from datetime import datetime

from data.fetcher import DataFetcher
from strategy.long_term.strategy import LongTermStrategy
from strategy.intraday.strategy import IntradayStrategy
from trading.engine import TradingEngine
from news.fetcher import NewsFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class QuantTradingSystem:
    """量化交易系统"""

    def __init__(self, config_path: str):
        """
        初始化系统

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        logger.info("=" * 50)
        logger.info("量化交易系统启动")
        logger.info("=" * 50)

        # 初始化各模块
        finnhub_key = self.config.get("quotes", {}).get("finnhub", {}).get("api_key", "")
        self.data_fetcher = DataFetcher(finnhub_key=finnhub_key)
        self.news_fetcher = NewsFetcher()

        # 长周期策略
        if self.config.get("strategy_long_term", {}).get("enabled"):
            self.long_term_strategy = LongTermStrategy(
                self.config  # 传递完整配置
            )
            logger.info("长周期策略已加载")

        # 日内策略
        if self.config.get("strategy_intraday", {}).get("enabled"):
            self.intraday_strategy = IntradayStrategy(
                self.config  # 传递完整配置
            )
            logger.info("日内策略已加载")

        # 交易引擎
        self.trading_engine = TradingEngine(self.config)
        logger.info("交易引擎已初始化")

        # 自选股列表
        self.hk_symbols = self.config["markets"]["hk"]["watchlist"]
        self.us_symbols = self.config["markets"]["us"]["watchlist"]

    def run_long_term_scan(self):
        """运行长周期扫描"""
        logger.info("\n" + "=" * 50)
        logger.info("开始长周期策略扫描")
        logger.info("=" * 50)

        # 扫描港股
        logger.info(f"扫描港股: {self.hk_symbols}")
        hk_df = self.long_term_strategy.scan(self.hk_symbols, "hk")

        # 扫描美股
        logger.info(f"扫描美股: {self.us_symbols}")
        us_df = self.long_term_strategy.scan(self.us_symbols, "us")

        # 合并结果
        if not hk_df.empty and not us_df.empty:
            all_df = pd.concat([hk_df, us_df], ignore_index=True)
            all_df = all_df.sort_values("total_score", ascending=False)
        elif not hk_df.empty:
            all_df = hk_df
        elif not us_df.empty:
            all_df = us_df
        else:
            logger.warning("没有扫描结果")
            return

        # 生成买入信号
        signals = self.long_term_strategy.generate_signals(all_df)
        
        # 过滤无效价格的信号
        signals = [s for s in signals if s.get("price", 0) > 0]

        logger.info(f"\n买入信号 ({len(signals)}个):")
        for s in signals:
            logger.info(f"  买入 {s['symbol']} {s['name']} 价格:{s['price']} 得分:{s['score']:.1f}")

        # 执行买入 (模拟)
        for signal in signals:
            # 检查是否已有持仓
            if signal["symbol"] in self.trading_engine.positions:
                continue

            # 获取当前价格 - 使用信号中指定的市场
            market = signal.get("market", "hk")
            quote = self.data_fetcher.get_quote(signal["symbol"], market)

            # 买入 (使用10%仓位)
            amount = self.trading_engine.cash * 0.10
            price = quote["price"] if quote and quote.get("price") else 0
            
            if price <= 0:
                logger.warning(f"跳过 {signal['symbol']}: 无效价格 {price}")
                continue
                
            result = self.trading_engine.buy(
                signal["symbol"],
                price,
                amount=amount,
                market=market
            )

        return signals

    def run_intraday_scan(self):
        """运行日内扫描"""
        logger.info("\n" + "=" * 50)
        logger.info("开始日内策略扫描")
        logger.info("=" * 50)

        # 扫描港股
        hk_df = self.intraday_strategy.scan(self.hk_symbols, "hk")
        hk_buys = hk_df[hk_df["action"] == "BUY"].head(3) if not hk_df.empty else pd.DataFrame()

        # 扫描美股
        us_df = self.intraday_strategy.scan(self.us_symbols, "us")
        us_buys = us_df[us_df["action"] == "BUY"].head(3) if not us_df.empty else pd.DataFrame()

        # 合并
        all_buys = pd.concat([hk_buys, us_buys], ignore_index=True)

        logger.info(f"\n日内买入信号 ({len(all_buys)}个):")
        for _, row in all_buys.iterrows():
            logger.info(f"  买入 {row['symbol']} 价格:{row['price']} 得分:{row['score']}")

        return all_buys

    def run_news(self):
        """获取新闻"""
        logger.info("\n" + "=" * 50)
        logger.info("获取财经新闻")
        logger.info("=" * 50)

        news = self.news_fetcher.get_combined_news()

        print("\n=== Yahoo Finance 美股 ===")
        yahoo_us = news.get("yahoo_us", [])
        for i, n in enumerate(yahoo_us[:5], 1):
            print(f"{i}. {n['title'][:60]}")

        print("\n=== BBC 商业 ===")
        bbc = news.get("bbc_business", [])
        for i, n in enumerate(bbc[:5], 1):
            print(f"{i}. {n['title'][:60]}")

        return news

    def check_positions(self):
        """检查持仓"""
        logger.info("\n" + "=" * 50)
        logger.info("检查持仓状态")
        logger.info("=" * 50)

        # 获取当前价格
        current_prices = {}
        for symbol in self.trading_engine.positions.keys():
            pos = self.trading_engine.positions[symbol]
            quote = self.data_fetcher.get_quote(symbol, pos["market"])
            if quote:
                current_prices[symbol] = quote["price"]

        # 检查组合
        portfolio = self.trading_engine.get_portfolio_value(current_prices)

        logger.info(f"\n总市值: {portfolio['total_value']:.2f}")
        logger.info(f"现金: {portfolio['cash']:.2f}")
        logger.info(f"持仓市值: {portfolio['position_value']:.2f}")
        logger.info(f"盈亏: {portfolio['pnl']:.2f} ({portfolio['pnl_pct']:.2f}%)")
        logger.info(f"持仓数量: {portfolio['num_positions']}")

        return portfolio

    def save_state(self):
        """保存状态"""
        self.trading_engine.save_state("/tmp/quant_trading_state.json")
        logger.info("状态已保存")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="量化交易系统")
    parser.add_argument("--config", "-c", default="config/config.yaml",
                       help="配置文件路径")
    parser.add_argument("--mode", "-m", choices=["all", "long", "intraday", "news", "check"],
                       default="all", help="运行模式")
    args = parser.parse_args()

    # 启动系统
    system = QuantTradingSystem(args.config)

    # 根据模式运行
    if args.mode == "all":
        # 全部运行
        system.run_news()
        system.run_long_term_scan()
        system.run_intraday_scan()
        system.check_positions()

    elif args.mode == "long":
        system.run_long_term_scan()

    elif args.mode == "intraday":
        system.run_intraday_scan()

    elif args.mode == "news":
        system.run_news()

    elif args.mode == "check":
        system.check_positions()

    # 保存状态
    system.save_state()

    logger.info("\n" + "=" * 50)
    logger.info("系统运行完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    import pandas as pd  # 需要在main中使用
    main()
