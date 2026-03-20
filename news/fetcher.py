#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻获取模块
功能: 从 Finnhub 获取财经新闻（更稳定）
作者: 虾虾 🦐
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    """新闻获取器 - 基于 Finnhub API"""

    def __init__(self, api_key: str = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"):
        """初始化"""
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"

    def get_market_news(self, category: str = "general") -> List[Dict]:
        """
        获取市场新闻

        Args:
            category: general/forex/crypto/merger/market

        Returns:
            List[Dict]: 新闻列表
        """
        try:
            url = f"{self.base_url}/news?category={category}&token={self.api_key}"
            r = requests.get(url, timeout=10)
            
            if r.status_code != 200:
                logger.error(f"获取新闻失败: HTTP {r.status_code}")
                return []
            
            news_list = r.json()
            
            results = []
            for n in news_list[:20]:  # 取前20条
                results.append({
                    "source": n.get("source", ""),
                    "title": n.get("headline", ""),
                    "summary": n.get("summary", "")[:200],
                    "url": n.get("url", ""),
                    "datetime": datetime.fromtimestamp(n.get("datetime", 0)).strftime("%Y-%m-%d %H:%M") if n.get("datetime") else ""
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            return []

    def get_stock_news(self, symbol: str) -> List[Dict]:
        """
        获取个股新闻

        Args:
            symbol: 股票代码，如 AAPL, TSLA

        Returns:
            List[Dict]: 新闻列表
        """
        try:
            url = f"{self.base_url}/news?category=general&token={self.api_key}&symbol={symbol}"
            r = requests.get(url, timeout=10)
            
            if r.status_code != 200:
                return []
            
            news_list = r.json()
            
            results = []
            for n in news_list[:10]:
                results.append({
                    "source": n.get("source", ""),
                    "title": n.get("headline", ""),
                    "summary": n.get("summary", "")[:200],
                    "url": n.get("url", ""),
                    "datetime": datetime.fromtimestamp(n.get("datetime", 0)).strftime("%Y-%m-%d %H:%M") if n.get("datetime") else ""
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取个股新闻失败: {e}")
            return []

    def get_tesla_news(self) -> List[Dict]:
        """获取特斯拉相关新闻"""
        all_news = self.get_market_news("general")
        
        tesla_news = []
        keywords = ["tesla", "tsla", "elon musk", "electric vehicle", "ev"]
        
        for n in all_news:
            title_lower = n.get("title", "").lower()
            if any(k in title_lower for k in keywords):
                tesla_news.append(n)
        
        return tesla_news[:10]

    def get_combined_news(self) -> Dict[str, List]:
        """获取组合新闻"""
        return {
            "market": self.get_market_news("general"),
            "forex": self.get_market_news("forex"),
            "crypto": self.get_market_news("crypto"),
        }

    def format_news_message(self, news_list: List[Dict], max_items: int = 5) -> str:
        """格式化新闻为消息"""
        if not news_list:
            return "暂无新闻"
        
        messages = []
        for i, news in enumerate(news_list[:max_items], 1):
            title = news.get("title", "N/A")[:60]
            source = news.get("source", "N/A")
            dt = news.get("datetime", "")
            
            messages.append(f"{i}. {title}")
            messages.append(f"   {source} | {dt}")
        
        return "\n".join(messages)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    fetcher = NewsFetcher()

    print("=== 市场新闻 ===")
    news = fetcher.get_market_news("general")
    print(f"获取到 {len(news)} 条新闻")
    for n in news[:5]:
        print(f"- {n['title'][:60]}")
        print(f"  {n['source']} | {n['datetime']}")

    print("\n=== 格式化测试 ===")
    print(fetcher.format_news_message(news))
