#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黄金买卖信号综合公式
======================

公式结构:
  S = w₁·T + w₂·G + w₃·O + w₄·R + w₅·C

其中:
  S  = 综合信号分数 (0-100)
  T  = 技术面得分
  G  = 地缘政治得分
  O  = 原油/通胀得分
  R  = 避险情绪得分
  C  = 加密货币/风险资产得分

权重分配:
  T  (技术面)  : 25%
  G  (地缘政治): 25%
  O  (原油)    : 20%
  R  (避险情绪): 20%
  C  (加密货币): 10%

====================================================
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

HSBC_PREMIUM = 1.09


# ==================== 权重配置 ====================
WEIGHTS = {
    "technical": 0.25,
    "geopolitical": 0.25,
    "oil": 0.20,
    "risk_sentiment": 0.20,
    "crypto": 0.10,
}


# ==================== 各因素评分函数 ====================

def score_technical(price: float, ma20: float, ma50: float, 
                     rsi: float, low_30d: float, high_30d: float) -> dict:
    """
    技术面评分 (0-100)
    
    子因素:
    - 均线位置 (MA20, MA50): 0-40分
    - RSI: 0-40分 (超卖高分)
    - 区间位置: 0-20分 (接近低点高分)
    """
    score = 0
    details = []
    
    # 均线位置 (40分)
    if price > ma20:
        ma_score = 40
        details.append(f"站上MA20(+40)")
    elif price > ma50:
        ma_score = 25
        details.append(f"高于MA50但低于MA20(+25)")
    else:
        ma_score = max(0, 20 - (ma50 - price) / (ma50 - ma20) * 20)
        details.append(f"低于双均线(+{ma_score:.0f})")
    score += ma_score
    
    # RSI (40分) - 超卖高分
    if rsi < 20:
        rsi_score = 40
        details.append(f"RSI严重超卖({rsi:.0f})(+40)")
    elif rsi < 30:
        rsi_score = 35
        details.append(f"RSI超卖({rsi:.0f})(+35)")
    elif rsi < 40:
        rsi_score = 25
        details.append(f"RSI偏低({rsi:.0f})(+25)")
    elif rsi > 80:
        rsi_score = 0
        details.append(f"RSI严重超买({rsi:.0f})(+0)")
    elif rsi > 70:
        rsi_score = 10
        details.append(f"RSI超买({rsi:.0f})(+10)")
    else:
        rsi_score = 20
        details.append(f"RSI中性({rsi:.0f})(+20)")
    score += rsi_score
    
    # 区间位置 (20分) - 30日低点附近高分
    range_pos = (price - low_30d) / (high_30d - low_30d)
    if range_pos < 0.2:  # 接近30日低点
        range_score = 20
        details.append(f"接近30日低点(+20)")
    elif range_pos < 0.4:
        range_score = 15
        details.append(f"低于区间中位(+15)")
    elif range_pos > 0.8:  # 接近30日高点
        range_score = 5
        details.append(f"接近30日高点(+5)")
    else:
        range_score = 10
        details.append(f"区间中位附近(+10)")
    score += range_score
    
    return {
        "score": min(100, max(0, score)),
        "details": details
    }


def score_geopolitical(geo_events: list) -> dict:
    """
    地缘政治评分 (0-100)
    
    子因素:
    - 中东战争/冲突: +30
    - 俄乌战争升级: +25
    - 台海紧张: +25
    - 美中贸易战: +15
    - 其他国际冲突: +10
    
    每次事件取最高权重，不叠加
    """
    if not geo_events:
        return {"score": 50, "details": ["无重大地缘政治事件(+50)"]}
    
    score = 50  # 基准分
    details = []
    
    # 高权重事件
    high_priority = ["中东", "战争", "以色列", "伊朗", "沙特", "俄乌", "乌克兰", "北约"]
    medium_priority = ["台海", "台湾", "中美", "贸易战", "关税", "制裁"]
    low_priority = ["朝鲜", "朝鲜半岛", "英国", "欧盟", "英国退欧"]
    
    max_add = 0
    for event in geo_events:
        event_str = str(event).upper()
        if any(k in event_str for k in [x.upper() for x in high_priority]):
            max_add = max(max_add, 50)  # +50
            details.append(f"重大: {event}(+50)")
        elif any(k in event_str for k in [x.upper() for x in medium_priority]):
            max_add = max(max_add, 30)  # +30
            details.append(f"中等: {event}(+30)")
        elif any(k in event_str for k in [x.upper() for x in low_priority]):
            max_add = max(max_add, 15)
            details.append(f"一般: {event}(+15)")
        else:
            max_add = max(max_add, 10)
            details.append(f"其他: {event}(+10)")
    
    score = min(100, score + max_add)
    return {"score": score, "details": details}


def score_oil(oil_price: float) -> dict:
    """
    原油/通胀评分 (0-100)
    
    逻辑: 原油涨 → 通胀预期涨 → 黄金受益
    
    - >100: 100分 (高通胀)
    - 80-100: 80分
    - 70-80: 65分
    - 50-70: 50分 (中性)
    - 30-50: 35分 (低通胀/通缩)
    - <30: 20分 (通缩)
    """
    if oil_price is None:
        return {"score": 50, "details": ["原油数据获取失败(+50)"]}
    
    if oil_price > 100:
        score = 100
        details = [f"原油${oil_price:.0f}>100 高通胀(+100)"]
    elif oil_price > 80:
        score = 80
        details = [f"原油${oil_price:.0f}>80 通胀压力(+80)"]
    elif oil_price > 70:
        score = 65
        details = [f"原油${oil_price:.0f}>70 中高油价(+65)"]
    elif oil_price > 50:
        score = 50
        details = [f"原油${oil_price:.0f} 中性区间(+50)"]
    elif oil_price > 30:
        score = 35
        details = [f"原油${oil_price:.0f}<50 低通胀警惕(+35)"]
    else:
        score = 20
        details = [f"原油${oil_price:.0f}<30 通缩风险(+20)"]
    
    return {"score": score, "details": details}


def score_risk_sentiment(vix: float, dxy: float) -> dict:
    """
    避险情绪评分 (0-100)
    
    子因素:
    - VIX恐慌指数: 0-50分
    - 美元指数: 0-50分
    
    VIX逻辑:
    - >40: 极度恐慌 +50
    - >30: 高度恐慌 +40
    - >20: 轻度恐慌 +30
    - 10-20: 正常 +20
    - <10: 极度平静 -10
    
    美元逻辑:
    - >105: 强美元 -20
    - >100: 偏强 -10
    - 90-100: 正常 0
    - <90: 弱美元 +20
    """
    vix_score = 0
    dxy_score = 0
    details = []
    
    # VIX评分
    if vix is None:
        vix_score = 20
        details.append("VIX数据获取失败(+20)")
    elif vix > 40:
        vix_score = 50
        details.append(f"VIX>{vix:.0f}极度恐慌(+50)")
    elif vix > 30:
        vix_score = 40
        details.append(f"VIX>{vix:.0f}高度恐慌(+40)")
    elif vix > 20:
        vix_score = 30
        details.append(f"VIX>{vix:.0f}轻度恐慌(+30)")
    elif vix < 10:
        vix_score = 10
        details.append(f"VIX<{vix:.0f}极度平静(+10)")
    else:
        vix_score = 20
        details.append(f"VIX={vix:.0f}正常区间(+20)")
    
    # 美元评分
    if dxy is None:
        dxy_score = 25
        details.append("美元指数获取失败(+25)")
    elif dxy > 110:
        dxy_score = 5
        details.append(f"美元>{dxy:.0f}极强(-15)")
    elif dxy > 105:
        dxy_score = 10
        details.append(f"美元>{dxy:.0f}强美元(-10)")
    elif dxy > 100:
        dxy_score = 15
        details.append(f"美元>{dxy:.0f}偏强(-5)")
    elif dxy < 90:
        dxy_score = 45
        details.append(f"美元<{dxy:.0f}弱美元(+20)")
    else:
        dxy_score = 25
        details.append(f"美元={dxy:.0f}中性(+0)")
    
    total = (vix_score + dxy_score) / 2
    return {"score": total, "details": details, "vix": vix, "dxy": dxy}


def score_crypto(btc_change_7d: float) -> dict:
    """
    加密货币/风险资产评分 (0-100)
    
    逻辑: BTC跌 → 避险情绪 → 黄金受益
          BTC涨 → 风险偏好 → 黄金承压
    
    - BTC 7日跌>20%: 100分 (强烈避险)
    - BTC 7日跌>10%: 80分
    - BTC 7日跌>5%: 60分
    - BTC 7日涨跌±5%: 50分 (中性)
    - BTC 7日涨>10%: 20分
    - BTC 7日涨>20%: 0分 (极度风险偏好)
    """
    if btc_change_7d is None:
        return {"score": 50, "details": ["BTC数据获取失败(+50)"]}
    
    change = btc_change_7d
    
    if change < -20:
        score = 100
        details = [f"BTC 7日{change:.0f}% 强烈避险(+100)"]
    elif change < -10:
        score = 80
        details = [f"BTC 7日{change:.0f}% 避险资金流入(+80)"]
    elif change < -5:
        score = 60
        details = [f"BTC 7日{change:.0f}% 偏弱避险(+60)"]
    elif change < 5:
        score = 50
        details = [f"BTC 7日{change:+.0f}% 中性区间(+50)"]
    elif change < 10:
        score = 30
        details = [f"BTC 7日{change:.0f}% 风险偏好(+30)"]
    elif change < 20:
        score = 15
        details = [f"BTC 7日{change:.0f}% 强风险偏好(+15)"]
    else:
        score = 0
        details = [f"BTC 7日{change:.0f}% 极度风险偏好(+0)"]
    
    return {"score": score, "details": details, "btc_change": btc_change_7d}


# ==================== 主计算函数 ====================

def calculate_final_score(
    tech: dict,
    geo: dict,
    oil: dict,
    risk: dict,
    crypto: dict
) -> dict:
    """
    综合评分计算
    
    公式:
    S = 0.25·T + 0.25·G + 0.20·O + 0.20·R + 0.10·C
    
    Args:
        tech: 技术面得分
        geo: 地缘政治得分
        oil: 原油得分
        risk: 避险情绪得分
        crypto: 加密货币得分
    
    Returns:
        dict: 最终评分和建议
    """
    
    # 计算加权分数
    raw_score = (
        WEIGHTS["technical"] * tech["score"] +
        WEIGHTS["geopolitical"] * geo["score"] +
        WEIGHTS["oil"] * oil["score"] +
        WEIGHTS["risk_sentiment"] * risk["score"] +
        WEIGHTS["crypto"] * crypto["score"]
    )
    
    # 归一化到0-100
    final_score = max(0, min(100, raw_score))
    
    # 信号评级
    if final_score >= 80:
        rating = "🟢 强烈买入"
        signal = "STRONG_BUY"
        action = "积极建仓，目标位分批卖出"
    elif final_score >= 65:
        rating = "🟡 买入"
        signal = "BUY"
        action = "可考虑买入，设好止损"
    elif final_score >= 50:
        rating = "⚪ 观望"
        signal = "HOLD"
        action = "等待更明确信号"
    elif final_score >= 35:
        rating = "🟠 卖出"
        signal = "SELL"
        action = "考虑减仓或止损"
    else:
        rating = "🔴 强烈卖出"
        signal = "STRONG_SELL"
        action = "清仓或做空，等待低位"
    
    return {
        "final_score": final_score,
        "rating": rating,
        "signal": signal,
        "action": action,
        "weights": WEIGHTS,
        "breakdown": {
            "technical": {"score": tech["score"], "weight": WEIGHTS["technical"], "contribution": WEIGHTS["technical"] * tech["score"]},
            "geopolitical": {"score": geo["score"], "weight": WEIGHTS["geopolitical"], "contribution": WEIGHTS["geopolitical"] * geo["score"]},
            "oil": {"score": oil["score"], "weight": WEIGHTS["oil"], "contribution": WEIGHTS["oil"] * oil["score"]},
            "risk_sentiment": {"score": risk["score"], "weight": WEIGHTS["risk_sentiment"], "contribution": WEIGHTS["risk_sentiment"] * risk["score"]},
            "crypto": {"score": crypto["score"], "weight": WEIGHTS["crypto"], "contribution": WEIGHTS["crypto"] * crypto["score"]},
        }
    }


def get_all_data() -> dict:
    """获取所有市场数据"""
    data = {}
    
    # 黄金
    try:
        gld = yf.Ticker("GLD")
        hist = gld.history(period="3mo")
        if not hist.empty:
            close = hist['Close'] * 10 * 7.8 * HSBC_PREMIUM
            data["gold_price"] = close.iloc[-1]
            data["ma20"] = close.rolling(20).mean().iloc[-1]
            data["ma50"] = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else close.iloc[-1]
            data["low_30d"] = close.rolling(30).min().iloc[-1]
            data["high_30d"] = close.rolling(30).max().iloc[-1]
            
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            data["rsi"] = (100 - (100 / (1 + rs))).iloc[-1]
    except:
        pass
    
    # 原油
    try:
        oil = yf.Ticker("BZ=F")
        hist = oil.history(period="1d")
        if not hist.empty:
            data["oil_price"] = hist['Close'].iloc[-1]
    except:
        data["oil_price"] = None
    
    # VIX
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1d")
        if not hist.empty:
            data["vix"] = hist['Close'].iloc[-1]
    except:
        data["vix"] = None
    
    # 美元指数
    try:
        dxy = yf.Ticker("DX-Y.NYB")
        hist = dxy.history(period="1d")
        if not hist.empty:
            data["dxy"] = hist['Close'].iloc[-1]
    except:
        try:
            eur = yf.Ticker("EURUSD=X")
            hist = eur.history(period="1d")
            if not hist.empty:
                data["dxy"] = 1 / hist['Close'].iloc[-1]
        except:
            pass
    
    # 比特币
    try:
        btc = yf.Ticker("BTC-USD")
        hist = btc.history(period="7d")
        if not hist.empty and len(hist) >= 5:
            data["btc_change_7d"] = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) * 100
    except:
        data["btc_change_7d"] = None
    
    return data


def run_analysis(geo_events: list = None):
    """运行完整分析"""
    if geo_events is None:
        geo_events = []
    
    print("=" * 60)
    print("黄金综合分析公式")
    print("=" * 60)
    print(f"\n公式: S = w₁T + w₂G + w₃O + w₄R + w₅C")
    print("权重: 技术25% + 地缘25% + 原油20% + 避险20% + 加密10%")
    print()
    
    # 获取数据
    data = get_all_data()
    
    print(f"📊 市场数据:")
    print(f"   金价: HK${data.get('gold_price', 'N/A'):.0f}" if data.get('gold_price') else "   金价: N/A")
    print(f"   MA20: HK${data.get('ma20', 'N/A'):.0f}" if data.get('ma20') else "   MA20: N/A")
    print(f"   RSI: {data.get('rsi', 'N/A'):.1f}" if data.get('rsi') else "   RSI: N/A")
    print(f"   原油: ${data.get('oil_price', 'N/A'):.2f}" if data.get('oil_price') else "   原油: N/A")
    print(f"   VIX: {data.get('vix', 'N/A'):.1f}" if data.get('vix') else "   VIX: N/A")
    print(f"   美元指数: {data.get('dxy', 'N/A'):.1f}" if data.get('dxy') else "   美元指数: N/A")
    print(f"   BTC 7日: {data.get('btc_change_7d', 'N/A'):+.1f}%" if data.get('btc_change_7d') else "   BTC 7日: N/A")
    print()
    
    # 计算各项得分
    tech_score = score_technical(
        price=data.get("gold_price", 0),
        ma20=data.get("ma20", 0),
        ma50=data.get("ma50", 0),
        rsi=data.get("rsi", 50),
        low_30d=data.get("low_30d", 0),
        high_30d=data.get("high_30d", 0)
    )
    
    geo_score = score_geopolitical(geo_events)
    oil_score = score_oil(data.get("oil_price"))
    risk_score = score_risk_sentiment(data.get("vix"), data.get("dxy"))
    crypto_score = score_crypto(data.get("btc_change_7d"))
    
    # 打印各项评分
    print("=" * 60)
    print("📈 各因素评分")
    print("=" * 60)
    
    for name, score_dict, weight in [
        ("技术面 (T)", tech_score, WEIGHTS["technical"]),
        ("地缘政治 (G)", geo_score, WEIGHTS["geopolitical"]),
        ("原油 (O)", oil_score, WEIGHTS["oil"]),
        ("避险情绪 (R)", risk_score, WEIGHTS["risk_sentiment"]),
        ("加密货币 (C)", crypto_score, WEIGHTS["crypto"]),
    ]:
        print(f"\n{name}: {score_dict['score']:.0f}/100 (权重{weight*100:.0f}%)")
        for detail in score_dict['details']:
            print(f"   {detail}")
    
    # 计算最终评分
    result = calculate_final_score(tech_score, geo_score, oil_score, risk_score, crypto_score)
    
    print()
    print("=" * 60)
    print("📋 综合评分")
    print("=" * 60)
    
    print(f"\n🏆 综合得分: {result['final_score']:.1f}/100")
    print(f"   评级: {result['rating']}")
    print(f"   信号: {result['signal']}")
    
    print(f"\n📊 权重贡献:")
    total = 0
    for factor, info in result["breakdown"].items():
        factor_names = {
            "technical": "技术面",
            "geopolitical": "地缘政治", 
            "oil": "原油",
            "risk_sentiment": "避险情绪",
            "crypto": "加密货币"
        }
        print(f"   {factor_names.get(factor, factor)}: {info['contribution']:.1f} ({info['weight']*100:.0f}% × {info['score']:.0f})")
        total += info['contribution']
    
    print(f"   ─────")
    print(f"   合计: {total:.1f}")
    
    print(f"\n💰 操作建议: {result['action']}")
    print()
    
    # 公式展示
    print("=" * 60)
    print("🔢 计算公式")
    print("=" * 60)
    formula = f"S = 0.25×{tech_score['score']:.0f} + 0.25×{geo_score['score']:.0f} + 0.20×{oil_score['score']:.0f} + 0.20×{risk_score['score']:.0f} + 0.10×{crypto_score['score']:.0f}"
    print(f"S = {result['final_score']:.1f}")
    print()
    
    return result


if __name__ == "__main__":
    # geo_events 可以手动传入新闻事件列表
    # 例如: run_analysis(["俄乌战争升级", "中东冲突"])
    run_analysis()
