#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块分析模块
支持热门板块监控和技术分析

作者: 虾虾 🦐
"""

import requests
import yfinance as yf
import pandas as pd
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 热门板块 ====================

SECTORS = {
    "储存/内存": {
        "description": "AI数据中心存储需求强劲，内存芯片短缺",
        "stocks": ["WDC", "STX", "MU", "PSTG", "RMBS", "SIMO"]
    },
    "储存板块(原)": {
        "description": "AI数据中心存储需求强劲",
        "stocks": ["WDC", "STX", "NTAP", "DELL", "HPE"]
    },
    "AI芯片": {
        "description": "人工智能算力需求爆发",
        "stocks": ["NVDA", "AMD", "INTC", "QCOM", "AVGO"]
    },
    "云服务": {
        "description": "云计算和企业软件",
        "stocks": ["MSFT", "AMZN", "GOOGL", "CRM", "NOW"]
    },
    "电动汽车": {
        "description": "新能源车和自动驾驶",
        "stocks": ["TSLA", "RIVN", "LCID", "NIO", "XPEV"]
    },
    "半导体设备": {
        "description": "芯片制造设备",
        "stocks": ["AMAT", "LRCX", "KLAC", "AMBA", "MU"]
    },
    "消费电子": {
        "description": "手机和电脑",
        "stocks": ["AAPL", "HPQ", "Dell", "SNE", "BBY"]
    }
}


def analyze_stock(code: str) -> Dict:
    """分析单只股票"""
    try:
        # Finnhub 实时行情
        token = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"
        r = requests.get(f"https://finnhub.io/api/v1/quote?symbol={code}&token={token}", timeout=5)
        quote = r.json()
        
        # Yahoo 技术指标
        stock = yf.Ticker(code)
        h = stock.history(period="3mo")
        
        if h.empty:
            return {"error": "无数据"}
        
        c = h['Close']
        
        # 计算指标
        ma5 = c.rolling(5).mean().iloc[-1]
        ma10 = c.rolling(10).mean().iloc[-1]
        ma20 = c.rolling(20).mean().iloc[-1]
        
        delta = c.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # 财报
        info = stock.info
        pe = info.get("trailingPE", 0)
        rev_growth = info.get("revenueGrowth", 0)
        
        return {
            "code": code,
            "price": quote.get("c", 0),
            "change": quote.get("dp", 0),
            "high": quote.get("h", 0),
            "low": quote.get("l", 0),
            "ma5": ma5,
            "ma10": ma10,
            "ma20": ma20,
            "rsi": rsi,
            "pe": pe,
            "revenue_growth": rev_growth * 100 if rev_growth else 0
        }
    except Exception as e:
        logger.error(f"分析失败 {code}: {e}")
        return {"code": code, "error": str(e)}


def analyze_sector(sector_name: str) -> Dict:
    """分析整个板块"""
    if sector_name not in SECTORS:
        return {"error": "未知板块"}
    
    sector = SECTORS[sector_name]
    stocks = sector["stocks"]
    
    results = []
    for code in stocks:
        data = analyze_stock(code)
        if "error" not in data:
            results.append(data)
    
    # 计算板块平均
    if results:
        avg_change = sum(r.get("change", 0) for r in results) / len(results)
        avg_rsi = sum(r.get("rsi", 50) for r in results) / len(results)
        
        # 找出最强和最弱
        sorted_by_change = sorted(results, key=lambda x: x.get("change", 0), reverse=True)
        
        return {
            "name": sector_name,
            "description": sector["description"],
            "stocks": results,
            "avg_change": avg_change,
            "avg_rsi": avg_rsi,
            "top_performer": sorted_by_change[0] if sorted_by_change else None,
            "worst_performer": sorted_by_change[-1] if sorted_by_change else None
        }
    
    return {"error": "无数据"}


def print_sector_report(sector_name: str):
    """打印板块报告"""
    result = analyze_sector(sector_name)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        return
    
    print("=" * 60)
    print(f"📊 {result['name']}")
    print(f"📝 {result['description']}")
    print("=" * 60)
    
    print(f"\n📈 板块平均涨跌幅: {result['avg_change']:.2f}%")
    print(f"📊 板块平均RSI: {result['avg_rsi']:.1f}")
    
    if result.get("top_performer"):
        t = result["top_performer"]
        print(f"\n🔥 最强: {t['code']} ({t['change']:.2f}%)")
    
    if result.get("worst_performer"):
        w = result["worst_performer"]
        print(f"❄️ 最弱: {w['code']} ({w['change']:.2f}%)")
    
    print(f"\n📋 详细数据:")
    print("-" * 60)
    print(f"{'代码':<8} {'价格':<10} {'涨跌':<10} {'RSI':<8} {'MA20':<10}")
    print("-" * 60)
    
    for r in sorted(result["stocks"], key=lambda x: x.get("change", 0), reverse=True):
        print(f"{r['code']:<8} ${r['price']:<9.2f} {r['change']:>+8.2f}% {r['rsi']:<8.1f} ${r.get('ma20', 0):<9.2f}")


# ==================== 测试 ====================
if __name__ == "__main__":
    # 分析储存板块
    print_sector_report("储存板块")
