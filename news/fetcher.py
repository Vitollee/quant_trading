#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻获取模块
功能: 从Yahoo Finance和BBC获取财经新闻
作者: 虾虾 🦐
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsFetcher:
    """新闻获取器"""

    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def get_yahoo_news(self, symbol: str = "", market: str = "hk") -> List[Dict]:
        """
        获取Yahoo Finance新闻

        Args:
            symbol: 股票代码
            market: 市场类型 "hk" 或 "us"

        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []

        try:
            if market == "hk":
                url = f"https://hk.finance.yahoo.com/quote/{symbol}/news"
            else:
                url = f"https://finance.yahoo.com/quote/{symbol}/news"

            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # 解析新闻条目
            articles = soup.find_all("li", {"class": "js-stream-content"})

            for article in articles[:10]:  # 取前10条
                try:
                    title_elem = article.find("h3")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    link = article.find("a")
                    href = "https://finance.yahoo.com" + link.get("href", "") if link else ""

                    # 获取摘要
                    summary_elem = article.find("p")
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    news_list.append({
                        "source": "Yahoo Finance",
                        "symbol": symbol,
                        "title": title,
                        "summary": summary[:200] if summary else "",
                        "url": href,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"获取Yahoo新闻失败: {e}")

        return news_list

    def get_yahoo_market_news(self, market: str = "us") -> List[Dict]:
        """
        获取市场新闻

        Args:
            market: 市场类型

        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []

        try:
            if market == "us":
                url = "https://finance.yahoo.com/topic/latest-news/"
            else:
                url = "https://hk.finance.yahoo.com/topic/latest-news/"

            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            articles = soup.find_all("li", {"class": "js-stream-content"})

            for article in articles[:15]:
                try:
                    title_elem = article.find("h3")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    summary_elem = article.find("p")
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    news_list.append({
                        "source": "Yahoo Finance",
                        "title": title,
                        "summary": summary[:200] if summary else "",
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"获取市场新闻失败: {e}")

        return news_list

    def get_bbc_news(self, category: str = "business") -> List[Dict]:
        """
        获取BBC新闻

        Args:
            category: 分类 (business, technology, world 等)

        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []

        try:
            url = f"https://www.bbc.com/news/{category}"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            articles = soup.find_all("article", {"class": "bbc-ukuv3"})

            for article in articles[:10]:
                try:
                    title_elem = article.find("h3")
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    link = article.find("a")
                    href = "https://www.bbc.com" + link.get("href", "") if link else ""

                    # 获取时间
                    time_elem = article.find("time")
                    time_str = time_elem.get("datetime", "") if time_elem else ""

                    news_list.append({
                        "source": "BBC",
                        "category": category,
                        "title": title,
                        "url": href,
                        "time": time_str
                    })
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"获取BBC新闻失败: {e}")

        return news_list

    def get_combined_news(self, keywords: Dict[str, List[str]] = None) -> Dict[str, List]:
        """
        获取组合新闻

        Args:
            keywords: 关键词字典 {"hk": ["港股", "A股"], "us": ["stock", "Fed"]}

        Returns:
            dict: 市场新闻汇总
        """
        results = {
            "yahoo_us": self.get_yahoo_market_news("us"),
            "yahoo_hk": self.get_yahoo_market_news("hk"),
            "bbc_business": self.get_bbc_news("business"),
            "bbc_tech": self.get_bbc_news("technology")
        }

        return results

    def format_news_message(self, news_list: List[Dict], max_items: int = 5) -> str:
        """
        格式化新闻为消息

        Args:
            news_list: 新闻列表
            max_items: 最大条目数

        Returns:
            str: 格式化后的消息
        """
        if not news_list:
            return "暂无新闻"

        messages = []
        for i, news in enumerate(news_list[:max_items], 1):
            title = news.get("title", "N/A")[:60]
            source = news.get("source", "N/A")
            time = news.get("time", "")

            messages.append(f"{i}. {title}")
            messages.append(f"   来源: {source} | {time}")

        return "\n".join(messages)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    fetcher = NewsFetcher()

    print("=== Yahoo 市场新闻 ===")
    news = fetcher.get_yahoo_market_news("us")
    print(f"获取到 {len(news)} 条新闻")
    for n in news[:3]:
        print(f"- {n['title'][:50]}")

    print("\n=== BBC 商业新闻 ===")
    news = fetcher.get_bbc_news("business")
    print(f"获取到 {len(news)} 条新闻")
    for n in news[:3]:
        print(f"- {n['title'][:50]}")

    print("\n=== 格式化测试 ===")
    news = fetcher.get_yahoo_market_news("us")
    print(fetcher.format_news_message(news))
