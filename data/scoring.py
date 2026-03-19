#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票评分系统
基于: 板块趋势、财报盈利、资金流向、PE、换手率

适用: 短线/波段交易 (1-30天)

评分权重:
- 板块趋势: 25%
- 财报盈利: 25%  
- 资金流向: 20%
- 市盈率: 15%
- 换手率: 10%
- 股价: 5%

作者: 虾虾 🦐
"""

import requests
import yfinance as yf
import pandas as pd
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== 配置 ====================

WEIGHTS = {
    "sector_momentum": 0.25,  # 板块趋势
    "profitability": 0.25,     # 财报盈利
    "capital_flow": 0.20,      # 资金流向
    "valuation": 0.15,         # 市盈率
    "liquidity": 0.10,         # 换手率
    "price": 0.05             # 股价位置
}

FINNHUB_TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"


# ==================== 评分函数 ====================

def get_price_score(price: float, ma20: float, ma50: float) -> float:
    """
    股价位置评分 (0-100)
    股价在均线之上 = 多头 = 高分
    """
    if not price or not ma20:
        return 50
    
    # 站上所有均线 = 100分
    # 跌破所有均线 = 0分
    score = 50
    if price > ma20:
        score += 25
    if price > ma50:
        score += 25
    
    return score


def get_pe_score(pe: float, sector_avg_pe: float = 20) -> float:
    """
    市盈率评分 (0-100)
    PE越低 = 分数越高
    """
    if not pe or pe <= 0:
        return 50  # 无数据给中间分
    
    if pe < sector_avg_pe * 0.7:
        return 100  # 严重低估
    elif pe < sector_avg_pe:
        return 75   # 低估
    elif pe < sector_avg_pe * 1.3:
        return 50   # 合理
    elif pe < sector_avg_pe * 1.5:
        return 25   # 高估
    else:
        return 10   # 严重高估


def get_volume_score(turnover_rate: float, avg_volume: int, volume: int) -> float:
    """
    换手率评分 (0-100)
    换手率适中最好，太高太低都不好
    """
    if not volume or not avg_volume:
        return 50
    
    ratio = volume / avg_volume
    
    # 1-3倍换手率 = 最佳
    if 1.0 <= ratio <= 3.0:
        return 100
    elif ratio > 5.0:
        return 60  # 太高可能过热
    elif ratio >= 0.5:
        return 75
    else:
        return 40


def get_profitability_score(info: dict) -> float:
    """
    盈利能力评分 (0-100)
    ROE、毛利率、营收增长
    """
    score = 0
    count = 0
    
    # ROE (权重最高)
    roe = info.get("returnOnEquity", 0)
    if roe:
        if roe > 0.20:
            score += 40
        elif roe > 0.15:
            score += 30
        elif roe > 0.10:
            score += 20
        elif roe > 0.05:
            score += 10
        count += 1
    
    # 毛利率
    marg = info.get("grossMargins", 0)
    if marg:
        if marg > 0.40:
            score += 30
        elif marg > 0.30:
            score += 20
        elif marg > 0.20:
            score += 10
        count += 1
    
    # 营收增长
    rev = info.get("revenueGrowth", 0)
    if rev:
        if rev > 0.30:
            score += 30
        elif rev > 0.20:
            score += 20
        elif rev > 0.10:
            score += 10
        count += 1
    
    if count == 0:
        return 50
    
    return min(100, score)


def get_capital_flow_score(price_change: float, volume: int) -> float:
    """
    资金流向评分 (0-100)
    涨跌幅 + 成交量
    """
    # 涨幅越大，资金流入可能性越高
    if price_change > 5:
        base = 100
    elif price_change > 2:
        base = 80
    elif price_change > 0:
        base = 60
    elif price_change > -2:
        base = 40
    else:
        base = 20
    
    # 成交量放大加分
    if volume > 10000000:  # 1000万股
        return min(100, base + 10)
    
    return base


def get_sector_momentum_score(code: str, sector_stocks: List[str]) -> float:
    """
    板块趋势评分 (0-100)
    如果板块多数上涨，个股也会受益
    """
    if not sector_stocks or code not in sector_stocks:
        return 50  # 未知板块给中间分
    
    try:
        # 获取板块其他股票走势
        changes = []
        for s in sector_stocks[:5]:  # 最多5只
            if s == code:
                continue
            r = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol={s}&token={FINNHUB_TOKEN}",
                timeout=5
            )
            d = r.json()
            if d.get("d"):
                changes.append(d.get("d", 0))
        
        if changes:
            avg_change = sum(changes) / len(changes)
            if avg_change > 3:
                return 100
            elif avg_change > 1:
                return 80
            elif avg_change > 0:
                return 60
            elif avg_change > -1:
                return 40
            else:
                return 20
    except:
        pass
    
    return 50


# ==================== 主函数 ====================

def score_stock(code: str, sector_stocks: List[str] = None) -> Dict:
    """
    给股票打分
    
    Args:
        code: 股票代码
        sector_stocks: 同板块其他股票列表
        
    Returns:
        dict: 评分结果
    """
    result = {
        "code": code,
        "total_score": 0,
        "details": {},
        "rating": ""
    }
    
    try:
        # 1. 获取实时数据
        r = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={code}&token={FINNHUB_TOKEN}",
            timeout=5
        )
        quote = r.json()
        
        price = quote.get("c", 0)
        change = quote.get("d", 0)
        change_pct = quote.get("dp", 0)
        volume = quote.get("v", 0)
        
        # 2. 获取历史数据计算技术指标
        stock = yf.Ticker(code)
        hist = stock.history(period="3mo")
        
        if hist.empty:
            return {"error": "无历史数据"}
        
        close = hist["Close"]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        
        # 3. 获取财报数据
        info = stock.info
        
        # 4. 计算各项得分
        scores = {}
        
        # 板块趋势 (25%)
        scores["sector_momentum"] = get_sector_momentum_score(code, sector_stocks)
        
        # 盈利能力 (25%)
        scores["profitability"] = get_profitability_score(info)
        
        # 资金流向 (20%)
        scores["capital_flow"] = get_capital_flow_score(change_pct, volume)
        
        # 市盈率 (15%)
        pe = info.get("trailingPE", 0)
        scores["valuation"] = get_pe_score(pe)
        
        # 换手率 (10%)
        avg_vol = hist["Volume"].tail(20).mean()
        scores["liquidity"] = get_volume_score(0, avg_vol, volume)
        
        # 股价位置 (5%)
        scores["price"] = get_price_score(price, ma20, ma50)
        
        # 5. 计算总分
        total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
        
        result["total_score"] = round(total, 1)
        result["details"] = {
            "price": price,
            "change_pct": change_pct,
            "pe": pe,
            "ma20": ma20,
            "ma50": ma50,
            "volume": volume,
            "scores": {k: round(v, 1) for k, v in scores.items()}
        }
        
        # 6. 评级
        if total >= 80:
            result["rating"] = "⭐⭐⭐ 强烈买入"
        elif total >= 65:
            result["rating"] = "⭐⭐ 买入"
        elif total >= 50:
            result["rating"] = "⭐ 观望"
        elif total >= 35:
            result["rating"] = "⚠️ 减仓"
        else:
            result["rating"] = "❌ 卖出"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def print_report(code: str, sector_stocks: List[str] = None):
    """打印评分报告"""
    result = score_stock(code, sector_stocks)
    
    if "error" in result:
        print(f"错误: {result['error']}")
        return
    
    print("=" * 60)
    print(f"📊 {code} 评分报告")
    print("=" * 60)
    
    d = result["details"]
    print(f"\n💰 当前价格: ${d['price']:.2f}")
    print(f"📈 涨跌幅: {d['change_pct']:+.2f}%")
    print(f"📊 市盈率: {d['pe']:.2f}" if d.get('pe') else "📊 市盈率: N/A")
    print(f"📉 MA20: ${d['ma20']:.2f}")
    print(f"📉 MA50: ${d['ma50']:.2f}")
    
    print(f"\n📋 分项得分:")
    for k, v in d["scores"].items():
        name = {
            "sector_momentum": "板块趋势",
            "profitability": "盈利能力",
            "capital_flow": "资金流向",
            "valuation": "市盈率",
            "liquidity": "换手率",
            "price": "股价位置"
        }.get(k, k)
        
        bar = "█" * int(v / 10) + "░" * (10 - int(v / 10))
        print(f"  {name}: {v:5.1f}/100 {bar}")
    
    print(f"\n🎯 总分: {result['total_score']}/100")
    print(f"📌 评级: {result['rating']}")
    print("=" * 60)


# ==================== 测试 ====================

if __name__ == "__main__":
    # 储存板块
    storage_sector = ["WDC", "STX", "MU", "PSTG", "RMBS", "SIMO"]
    
    print("\n" + "=" * 60)
    print("🎯 储存板块股票评分 (短线/波段)")
    print("=" * 60)
    
    results = []
    for code in storage_sector:
        r = score_stock(code, storage_sector)
        if "error" not in r:
            results.append(r)
    
    # 按总分排序
    results.sort(key=lambda x: x["total_score"], reverse=True)
    
    print("\n📊 板块排名:\n")
    print(f"{'排名':<4} {'代码':<6} {'总分':<6} {'评级'}")
    print("-" * 40)
    for i, r in enumerate(results, 1):
        print(f"{i:<4} {r['code']:<6} {r['total_score']:<6.1f} {r['rating']}")
    
    # 详细分析第一名
    if results:
        print(f"\n📝 详细分析 - {results[0]['code']}")
        print_report(results[0]["code"], storage_sector)
