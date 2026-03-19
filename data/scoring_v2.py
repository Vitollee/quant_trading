#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票评分系统 - 长线/价值投资版
基于: 盈利能力、市盈率、板块趋势、资金流向、换手率、股价

适用: 长线投资 (1年以上)

评分权重:
- 盈利能力: 30%  (ROE、毛利率、营收增长)
- 市盈率: 25%   (估值合理)
- 板块趋势: 15%  (行业前景)
- 资金流向: 10% (机构持仓)
- 换手率: 10%  (流动性)
- 股价位置: 10% (择时)

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

# 长线权重
WEIGHTS_LONG = {
    "profitability": 0.30,   # 盈利能力
    "valuation": 0.25,        # 市盈率
    "sector_momentum": 0.15,  # 板块趋势
    "capital_flow": 0.10,     # 资金流向
    "liquidity": 0.10,        # 换手率
    "price": 0.10            # 股价位置
}

# 短线权重
WEIGHTS_SHORT = {
    "sector_momentum": 0.25,  # 板块趋势
    "profitability": 0.25,    # 盈利能力
    "capital_flow": 0.20,     # 资金流向
    "valuation": 0.15,        # 市盈率
    "liquidity": 0.10,        # 换手率
    "price": 0.05            # 股价位置
}

FINNHUB_TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"


# ==================== 评分函数 ====================

def get_long_term_valuation_score(pe: float, fwd_pe: float, sector_avg_pe: float = 20) -> float:
    """
    长线估值评分 (0-100)
    用预期PE更重要
    """
    if not pe or pe <= 0:
        return 50
    
    # 预期PE更准确
    if fwd_pe and fwd_pe > 0:
        use_pe = fwd_pe
    else:
        use_pe = pe
    
    if use_pe < sector_avg_pe * 0.6:
        return 100  # 严重低估
    elif use_pe < sector_avg_pe * 0.8:
        return 85   # 低估
    elif use_pe < sector_avg_pe:
        return 70   # 合理偏低
    elif use_pe < sector_avg_pe * 1.3:
        return 50   # 合理
    elif use_pe < sector_avg_pe * 1.5:
        return 30   # 偏贵
    else:
        return 15    # 贵


def get_long_term_profitability_score(info: dict) -> float:
    """
    长线盈利能力评分 (0-100)
    更注重持续性和稳定性
    """
    score = 0
    count = 0
    
    # ROE - 最重要
    roe = info.get("returnOnEquity", 0)
    if roe:
        if roe > 0.25:
            score += 35
        elif roe > 0.20:
            score += 30
        elif roe > 0.15:
            score += 25
        elif roe > 0.10:
            score += 15
        elif roe > 0.05:
            score += 10
        count += 1
    
    # 毛利率
    marg = info.get("grossMargins", 0)
    if marg:
        if marg > 0.50:
            score += 25
        elif marg > 0.40:
            score += 20
        elif marg > 0.30:
            score += 15
        elif marg > 0.20:
            score += 10
        count += 1
    
    # 营收增长 - 连续性
    rev = info.get("revenueGrowth", 0)
    if rev:
        if rev > 0.30:
            score += 25
        elif rev > 0.20:
            score += 20
        elif rev > 0.10:
            score += 15
        elif rev > 0.05:
            score += 10
        count += 1
    
    # 盈利增长
    earn = info.get("earningsGrowth", 0)
    if earn:
        if earn > 0.30:
            score += 15
        elif earn > 0.15:
            score += 10
        elif earn > 0:
            score += 5
        count += 1
    
    if count == 0:
        return 50
    
    return min(100, score)


def get_short_term_profitability_score(info: dict) -> float:
    """
    短线盈利能力评分 (0-100)
    更注重增长弹性
    """
    score = 0
    count = 0
    
    # 营收增长 - 短线最重要
    rev = info.get("revenueGrowth", 0)
    if rev:
        if rev > 0.50:
            score += 35
        elif rev > 0.30:
            score += 30
        elif rev > 0.20:
            score += 20
        elif rev > 0.10:
            score += 10
        count += 1
    
    # 盈利增长
    earn = info.get("earningsGrowth", 0)
    if earn:
        if earn > 0.50:
            score += 30
        elif earn > 0.30:
            score += 25
        elif earn > 0.15:
            score += 15
        elif earn > 0:
            score += 10
        count += 1
    
    # 毛利率
    marg = info.get("grossMargins", 0)
    if marg:
        if marg > 0.40:
            score += 20
        elif marg > 0.30:
            score += 15
        elif marg > 0.20:
            score += 10
        count += 1
    
    # ROE
    roe = info.get("returnOnEquity", 0)
    if roe:
        if roe > 0.15:
            score += 15
        elif roe > 0.10:
            score += 10
        count += 1
    
    if count == 0:
        return 50
    
    return min(100, score)


def get_valuation_score(pe: float, sector_avg_pe: float = 20) -> float:
    """短线估值评分"""
    if not pe or pe <= 0:
        return 50
    
    if pe < sector_avg_pe * 0.7:
        return 100
    elif pe < sector_avg_pe:
        return 75
    elif pe < sector_avg_pe * 1.3:
        return 50
    elif pe < sector_avg_pe * 1.5:
        return 25
    else:
        return 10


def get_liquidity_score(avg_volume: int) -> float:
    """换手率评分"""
    if avg_volume > 50000000:  # 5000万股
        return 100
    elif avg_volume > 20000000:
        return 80
    elif avg_volume > 10000000:
        return 60
    elif avg_volume > 5000000:
        return 40
    else:
        return 20


def get_price_position_score(price: float, ma20: float, ma50: float, ma200: float) -> float:
    """股价位置评分"""
    if not price:
        return 50
    
    score = 50
    if ma20 and price > ma20:
        score += 15
    if ma50 and price > ma50:
        score += 15
    if ma200 and price > ma200:
        score += 20
    
    return min(100, score)


def get_capital_flow_score(price_change: float) -> float:
    """资金流向评分"""
    if price_change > 5:
        return 100
    elif price_change > 2:
        return 80
    elif price_change > 0:
        return 60
    elif price_change > -2:
        return 40
    else:
        return 20


def get_sector_score(code: str, sector_stocks: list) -> float:
    """板块评分"""
    if not sector_stocks:
        return 50
    
    try:
        changes = []
        for s in sector_stocks[:5]:
            if s == code:
                continue
            r = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol={s}&token={FINNHUB_TOKEN}",
                timeout=3
            )
            d = r.json()
            if d.get("d"):
                changes.append(d.get("d", 0))
        
        if changes:
            avg = sum(changes) / len(changes)
            if avg > 3:
                return 100
            elif avg > 1:
                return 75
            elif avg > 0:
                return 60
            elif avg > -1:
                return 40
            else:
                return 20
    except:
        pass
    
    return 50


# ==================== 主函数 ====================

def score_stock_long(code: str, sector_stocks: list = None) -> Dict:
    """长线评分"""
    return score_stock(code, sector_stocks, is_long_term=True)


def score_stock_short(code: str, sector_stocks: list = None) -> Dict:
    """短线评分"""
    return score_stock(code, sector_stocks, is_long_term=False)


def score_stock(code: str, sector_stocks: list = None, is_long_term: bool = True) -> Dict:
    """综合评分"""
    
    weights = WEIGHTS_LONG if is_long_term else WEIGHTS_SHORT
    result = {
        "code": code,
        "type": "长线" if is_long_term else "短线",
        "total_score": 0,
        "details": {},
        "rating": ""
    }
    
    try:
        # 实时行情
        r = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={code}&token={FINNHUB_TOKEN}",
            timeout=5
        )
        quote = r.json()
        
        price = quote.get("c", 0)
        change_pct = quote.get("dp", 0)
        volume = quote.get("v", 0)
        
        # 历史数据
        stock = yf.Ticker(code)
        hist = stock.history(period="1y")
        
        if hist.empty:
            return {"error": "无历史数据"}
        
        close = hist["Close"]
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else ma50
        avg_vol = hist["Volume"].tail(60).mean()
        
        # 财报
        info = stock.info
        pe = info.get("trailingPE", 0)
        fwd_pe = info.get("forwardPE", 0)
        
        # 计算各项得分
        scores = {}
        
        if is_long_term:
            scores["profitability"] = get_long_term_profitability_score(info)
            scores["valuation"] = get_long_term_valuation_score(pe, fwd_pe)
        else:
            scores["profitability"] = get_short_term_profitability_score(info)
            scores["valuation"] = get_valuation_score(pe)
        
        scores["sector_momentum"] = get_sector_score(code, sector_stocks)
        scores["capital_flow"] = get_capital_flow_score(change_pct)
        scores["liquidity"] = get_liquidity_score(avg_vol)
        scores["price"] = get_price_position_score(price, ma20, ma50, ma200)
        
        # 总分
        total = sum(scores[k] * weights[k] for k in weights)
        
        result["total_score"] = round(total, 1)
        result["details"] = {
            "price": price,
            "change_pct": change_pct,
            "pe": pe,
            "fwd_pe": fwd_pe,
            "ma20": ma20,
            "ma50": ma50,
            "ma200": ma200,
            "avg_volume": avg_vol,
            "scores": {k: round(v, 1) for k, v in scores.items()}
        }
        
        # 评级
        if total >= 80:
            result["rating"] = "⭐⭐⭐ 强烈推荐"
        elif total >= 65:
            result["rating"] = "⭐⭐ 推荐买入"
        elif total >= 50:
            result["rating"] = "⭐ 观望"
        elif total >= 35:
            result["rating"] = "⚠️ 建议回避"
        else:
            result["rating"] = "❌ 不推荐"
        
    except Exception as e:
        result["error"] = str(e)
    
    return result


def print_report(code: str, sector_stocks: list = None):
    """打印对比报告"""
    long = score_stock_long(code, sector_stocks)
    short = score_stock_short(code, sector_stocks)
    
    print("=" * 65)
    print(f"📊 {code} 综合评分报告")
    print("=" * 65)
    
    if "error" in long:
        print(f"错误: {long['error']}")
        return
    
    # 长线
    print(f"\n📈 长线评分 (1年以上)")
    print(f"   总分: {long['total_score']}/100 - {long['rating']}")
    print(f"   盈利能力: {long['details']['scores']['profitability']}/100")
    print(f"   估值: {long['details']['scores']['valuation']}/100")
    print(f"   板块趋势: {long['details']['scores']['sector_momentum']}/100")
    
    # 短线
    print(f"\n📉 短线评分 (1-30天)")
    print(f"   总分: {short['total_score']}/100 - {short['rating']}")
    print(f"   板块趋势: {short['details']['scores']['sector_momentum']}/100")
    print(f"   盈利能力: {short['details']['scores']['profitability']}/100")
    print(f"   资金流向: {short['details']['scores']['capital_flow']}/100")
    
    # 当前数据
    d = long["details"]
    print(f"\n💰 当前价格: ${d['price']:.2f}")
    print(f"📈 涨跌幅: {d['change_pct']:+.2f}%")
    print(f"📊 市盈率: {d['pe']:.2f}" if d.get('pe') else "📊 市盈率: N/A")
    print(f"📊 预期PE: {d['fwd_pe']:.2f}" if d.get('fwd_pe') else "📊 预期PE: N/A")
    
    # 建议
    print(f"\n💡 建议:")
    if long["total_score"] >= 65:
        print(f"   �_LONG: 长线价值投资 - {long['rating']}")
    if short["total_score"] >= 65:
        print(f"   📉 短线交易 - {short['rating']}")
    if long["total_score"] < 50 and short["total_score"] < 50:
        print("   ⚠️ 当前不建议买入")
    
    print("=" * 65)


def print_ranking(codes: list, sector_stocks: list = None):
    """打印排名"""
    print("\n" + "=" * 65)
    print("🎯 股票评分排名")
    print("=" * 65)
    
    long_results = []
    short_results = []
    
    for code in codes:
        long = score_stock_long(code, sector_stocks)
        short = score_stock_short(code, sector_stocks)
        
        if "error" not in long:
            long_results.append(long)
        if "error" not in short:
            short_results.append(short)
    
    # 排序
    long_results.sort(key=lambda x: x["total_score"], reverse=True)
    short_results.sort(key=lambda x: x["total_score"], reverse=True)
    
    print("\n📈 长线排名 (价值投资):")
    print(f"{'排名':<4} {'代码':<6} {'总分':<6} {'评级'}")
    print("-" * 40)
    for i, r in enumerate(long_results[:5], 1):
        print(f"{i:<4} {r['code']:<6} {r['total_score']:<6.1f} {r['rating']}")
    
    print("\n📉 短线排名 (波段交易):")
    print(f"{'排名':<4} {'代码':<6} {'总分':<6} {'评级'}")
    print("-" * 40)
    for i, r in enumerate(short_results[:5], 1):
        print(f"{i:<4} {r['code']:<6} {r['total_score']:<6.1f} {r['rating']}")


# ==================== 测试 ====================

if __name__ == "__main__":
    # 储存板块
    storage = ["WDC", "STX", "MU", "PSTG", "RMBS", "SIMO"]
    
    # 打印排名
    print_ranking(storage, storage)
    
    # 详细分析 MU
    print("\n")
    print_report("MU", storage)
