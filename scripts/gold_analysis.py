#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黄金综合分析系统
综合地缘政治、原油、避险情绪、加密货币判断买卖信号

作者: 虾虾 🦐
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import requests

# HSBC银行价溢价
HSBC_PREMIUM = 1.09


def get_gold_price():
    """获取金价（港币/盎司）"""
    try:
        gld = yf.Ticker("GLD")
        hist = gld.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1] * 10 * 7.8 * HSBC_PREMIUM
            return price
    except:
        pass
    return None


def get_gold_technical():
    """获取黄金技术指标"""
    try:
        gld = yf.Ticker("GLD")
        hist = gld.history(period="3mo")
        if hist.empty:
            return None
        
        close = hist['Close'] * 10 * 7.8 * HSBC_PREMIUM
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else close.iloc[-1]
        low_30d = close.rolling(30).min().iloc[-1]
        high_30d = close.rolling(30).max().iloc[-1]
        
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        return {
            "price": close.iloc[-1],
            "ma20": ma20,
            "ma50": ma50,
            "low_30d": low_30d,
            "high_30d": high_30d,
            "rsi": rsi,
            "above_ma20": close.iloc[-1] > ma20,
            "above_ma50": close.iloc[-1] > ma50,
        }
    except:
        return None


def get_oil_price():
    """获取原油价格（布伦特原油，美元）"""
    try:
        oil = yf.Ticker("BZ=F")  # Brent Crude
        hist = oil.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        pass
    
    # 备用：XOM ETF 近似
    try:
        xom = yf.Ticker("XOM")
        hist = xom.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1] * 3  # 粗略估算
    except:
        pass
    return None


def get_dxy_index():
    """获取美元指数 DXY"""
    try:
        dxy = yf.Ticker("DX-Y.NYB")
        hist = dxy.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        pass
    
    # 备用：EUR/USD 反推
    try:
        eur = yf.Ticker("EURUSD=X")
        hist = eur.history(period="5d")
        if not hist.empty:
            return 1 / hist['Close'].iloc[-1]
    except:
        pass
    return None


def get_vix():
    """获取VIX恐慌指数"""
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        pass
    return None


def get_btc_price():
    """获取比特币价格（风险情绪指标）"""
    try:
        btc = yf.Ticker("BTC-USD")
        hist = btc.history(period="5d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
    except:
        pass
    return None


def get_risk_sentiment():
    """综合评估风险情绪"""
    vix = get_vix()
    dxy = get_dxy_index()
    btc = get_btc_price()
    
    sentiment = "NEUTRAL"
    score = 0
    details = []
    
    # VIX分析 (>20恐慌, >30极度恐慌)
    if vix:
        details.append(f"VIX: {vix:.1f}")
        if vix > 30:
            sentiment = "RISK_OFF"
            score += 3
            details.append("极度恐慌 ↑利好黄金")
        elif vix > 20:
            sentiment = "RISK_OFF"
            score += 2
            details.append("市场恐慌 ↑利好黄金")
        elif vix < 15:
            sentiment = "RISK_ON"
            score -= 1
            details.append("市场平静 ↓利空黄金")
        else:
            score += 0
    
    # 美元指数分析 (>100强美元, <100弱美元)
    if dxy:
        details.append(f"美元指数: {dxy:.1f}")
        if dxy > 105:
            score -= 2
            details.append("强美元 ↓利空黄金")
        elif dxy < 95:
            score += 2
            details.append("弱美元 ↑利好黄金")
    
    # BTC分析 (BTC涨=风险偏好, BTC跌=避险)
    btc_change = None
    try:
        btc = yf.Ticker("BTC-USD")
        hist = btc.history(period="5d")
        if not hist.empty and len(hist) >= 5:
            btc_change = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) * 100
            details.append(f"BTC 5日: {btc_change:+.1f}%")
            if btc_change < -10:
                score += 2
                details.append("BTC大跌 ↑避险资金流入黄金")
            elif btc_change < -5:
                score += 1
                details.append("BTC下跌 ↑避险情绪")
            elif btc_change > 10:
                score -= 2
                details.append("BTC大涨 ↓资金流向风险资产")
            elif btc_change > 5:
                score -= 1
                details.append("BTC上涨 ↓风险偏好")
    except:
        pass
    
    return sentiment, score, details


def get_geopolitical_score():
    """评估地缘政治风险"""
    # 地缘政治新闻评分 (手动更新，或接入新闻API)
    # 这里用简化版：检查最近重大事件
    
    score = 0
    events = []
    
    # 中东局势（原油供应影响）
    # 俄乌战争
    # 美中贸易关系
    # 台海局势
    # 美联储政策
    
    # 这部分需要接入新闻API实时分析
    # 目前返回基准分数
    
    return score, events


def get_oil_gold_correlation():
    """原油与黄金相关性分析"""
    oil = get_oil_price()
    gold = get_gold_price()
    
    if not oil or not gold:
        return None, None, "数据不足"
    
    # 历史相关性（简化计算）
    correlation = "正相关"
    analysis = ""
    
    # 黄金和原油通常正相关（通胀预期）
    if oil > 80:
        analysis = f"原油${oil:.0f}>80 高油价→通胀↑→利好黄金"
    elif oil < 50:
        analysis = f"原油${oil:.0f}<50 低油价→通缩预期→利空黄金"
    else:
        analysis = f"原油${oil:.0f} 中性区间"
    
    return oil, gold, analysis


def calculate_gold_score():
    """综合评分计算"""
    print("=" * 50)
    print("黄金综合分析报告")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)
    
    results = {}
    
    # 1. 黄金价格和技术指标
    gold = get_gold_price()
    tech = get_gold_technical()
    
    print(f"\n📊 黄金价格和技术指标:")
    if gold:
        print(f"   金价: HK${gold:.0f}/oz")
        results['gold_price'] = gold
    if tech:
        print(f"   20日均线: HK${tech['ma20']:.0f}")
        print(f"   50日均线: HK${tech['ma50']:.0f}")
        print(f"   30日低/高: {tech['low_30d']:.0f} / {tech['high_30d']:.0f}")
        print(f"   RSI(14): {tech['rsi']:.1f}")
        print(f"   {'✅' if tech['above_ma20'] else '❌'} 站上20日均线" if tech['above_ma20'] else f"   ❌ 低于20日均线({(1-tech['price']/tech['ma20'])*100:.1f}%)")
        results['technical'] = tech
    else:
        print("   无法获取技术数据")
    
    # 2. 原油价格
    print(f"\n🛢️ 原油价格:")
    oil, gold_for_oil, oil_analysis = get_oil_gold_correlation()
    if oil:
        print(f"   布伦特原油: ${oil:.2f}")
        print(f"   分析: {oil_analysis}")
        results['oil'] = oil
    else:
        print("   无法获取原油数据")
    
    # 3. 风险情绪
    print(f"\n😨 风险情绪指标:")
    sentiment, sentiment_score, sentiment_details = get_risk_sentiment()
    sentiment_emoji = {"RISK_OFF": "🔴", "RISK_ON": "🟢", "NEUTRAL": "🟡"}
    print(f"   情绪状态: {sentiment_emoji.get(sentiment, '⚪')} {sentiment}")
    print(f"   详情: {', '.join(sentiment_details)}")
    results['sentiment'] = sentiment
    results['sentiment_score'] = sentiment_score
    
    # 4. 地缘政治（简化）
    print(f"\n🌍 地缘政治:")
    geo_score, geo_events = get_geopolitical_score()
    if geo_events:
        for event in geo_events:
            print(f"   - {event}")
    else:
        print("   无重大事件（建议接入新闻API）")
    results['geopolitical_score'] = geo_score
    
    # 5. 综合评分
    print(f"\n{'='*50}")
    print(f"📈 综合评分")
    print(f"{'='*50}")
    
    total_score = 0
    max_score = 0
    breakdown = []
    
    # 技术面 (30%)
    if tech:
        max_score += 30
        tech_score = 0
        
        # RSI (超卖=买入信号)
        if tech['rsi'] < 30:
            tech_score += 15
            breakdown.append(f"RSI超卖({tech['rsi']:.0f}) +15")
        elif tech['rsi'] < 40:
            tech_score += 8
            breakdown.append(f"RSI偏低({tech['rsi']:.0f}) +8")
        elif tech['rsi'] > 70:
            tech_score -= 10
            breakdown.append(f"RSI超买({tech['rsi']:.0f}) -10")
        
        # 均线位置
        if tech['above_ma20']:
            tech_score += 10
            breakdown.append("站上20日均线 +10")
        else:
            tech_score -= 5
            breakdown.append(f"低于20日均线 -5")
        
        if tech['above_ma50']:
            tech_score += 5
            breakdown.append("站上50日均线 +5")
        
        # 30日区间位置
        range_pos = (tech['price'] - tech['low_30d']) / (tech['high_30d'] - tech['low_30d']) * 100
        if range_pos < 30:
            tech_score += 5
            breakdown.append(f"接近30日低点 +5")
        
        total_score += tech_score
        breakdown.append(f"技术面小计: {tech_score}/{30}")
    
    # 避险情绪 (30%)
    max_score += 30
    total_score += sentiment_score * 3  # scale to 30
    breakdown.append(f"避险情绪×3: {sentiment_score*3}/30 ({sentiment})")
    
    # 原油 (20%)
    max_score += 20
    if oil:
        if oil > 90:
            oil_score = 15
            breakdown.append(f"高油价(>90) +15")
        elif oil > 70:
            oil_score = 10
            breakdown.append(f"中高油价(>70) +10")
        elif oil < 50:
            oil_score = -10
            breakdown.append(f"低油价(<50) -10")
        else:
            oil_score = 5
            breakdown.append(f"中性油价 +5")
        total_score += oil_score
        breakdown.append(f"原油小计: {oil_score}/20")
    
    # 地缘政治 (20%)
    max_score += 20
    total_score += geo_score * 5  # scale to 20
    breakdown.append(f"地缘政治×5: {geo_score*5}/20")
    
    # 打印 breakdown
    print(f"\n评分明细:")
    for item in breakdown:
        print(f"   {item}")
    
    # 最终评分 (0-100)
    final_score = max(0, min(100, 50 + total_score / max_score * 50))
    
    print(f"\n🏆 综合评分: {final_score:.0f}/100")
    
    # 评级
    if final_score >= 75:
        rating = "🟢 强烈买入"
        action = "SIGNAL_BUY_STRONG"
    elif final_score >= 60:
        rating = "🟡 买入"
        action = "SIGNAL_BUY"
    elif final_score >= 45:
        rating = "⚪ 观望"
        action = "SIGNAL_HOLD"
    elif final_score >= 30:
        rating = "🟠 卖出"
        action = "SIGNAL_SELL"
    else:
        rating = "🔴 强烈卖出"
        action = "SIGNAL_SELL_STRONG"
    
    print(f"   评级: {rating}")
    
    # 交易信号
    print(f"\n{'='*50}")
    print(f"📋 交易信号")
    print(f"{'='*50}")
    
    signals = []
    
    # 买入信号
    if final_score >= 60:
        signals.append("✅ 综合评分支持买入")
    elif final_score < 40:
        signals.append("⚠️ 综合评分偏弱，建议观望或减仓")
    
    # 技术面确认
    if tech:
        if tech['rsi'] < 35 and sentiment_score >= 1:
            signals.append("✅ RSI超卖 + 避险情绪 → 买入信号")
        if not tech['above_ma20'] and gold < tech['ma20']:
            signals.append("⚠️ 价格低于均线，短期偏弱")
    
    # 风险情绪确认
    if sentiment == "RISK_OFF" and sentiment_score >= 2:
        signals.append("✅ 避险情绪高涨 → 利好黄金")
    
    # 原油确认
    if oil and oil > 80:
        signals.append("✅ 高油价 → 通胀预期 → 利好黄金")
    
    for sig in signals:
        print(f"   {sig}")
    
    print(f"\n{'='*50}")
    print(f"💰 操作建议")
    print(f"{'='*50}")
    
    if action in ["SIGNAL_BUY_STRONG", "SIGNAL_BUY"]:
        print(f"   {rating}")
        print(f"   综合评分: {final_score:.0f}/100")
        print(f"   建议: 可考虑分批买入，止损设30日低点下方")
    elif action == "SIGNAL_HOLD":
        print(f"   评级: {rating}")
        print(f"   建议: 等待更明确信号")
    else:
        print(f"   {rating}")
        print(f"   综合评分: {final_score:.0f}/100")
        print(f"   建议: 减仓或止损，等待低位机会")
    
    print(f"\n{'='*50}")
    
    return {
        "score": final_score,
        "rating": rating,
        "action": action,
        "gold_price": gold,
        "sentiment": sentiment,
        "oil_price": oil,
        "signals": signals,
        "tech": tech
    }


if __name__ == "__main__":
    result = calculate_gold_score()
