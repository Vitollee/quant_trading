#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黄金综合评分公式 v2
======================

公式结构:
  S = w₁·T + w₂·O + w₃·R

其中:
  S  = 综合信号分数 (0-100)
  T  = 技术面得分 (权重 25%)
  O  = 原油/通胀得分 (权重 20%)
  R  = 避险情绪得分 (权重 55%)

====================================================
避险情绪 R 包含:
  - 地缘政治 G (25%): 战争/冲突/制裁/贸易战
  - VIX恐慌指数 (20%): 市场波动率
  - 美元指数 DXY (15%): 美元强弱
  - 加密货币 (15%): BTC走势代表风险偏好
  - 美债收益率 (15%): 利率变化
  - 信用利差 (10%): 企业债信用差

====================================================
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

HSBC_PREMIUM = 1.09


# ==================== 权重配置 ====================
WEIGHTS = {
    "technical": 0.25,
    "oil": 0.20,
    "risk_sentiment": 0.55,
}

# 避险情绪子权重 (必须相加=100%)
RISK_SUBSCORE_WEIGHTS = {
    "geopolitical": 0.25,
    "vix": 0.20,
    "dxy": 0.15,
    "crypto": 0.15,
    "bond_yield": 0.15,
    "credit_spread": 0.10,
}


# ==================== 1. 技术面评分 ====================

def score_technical(price: float, ma20: float, ma50: float, 
                     rsi: float, low_30d: float, high_30d: float) -> dict:
    """
    技术面评分 (0-100, 越高越支持买入)
    
    子因素 (各占不同权重):
    - 均线位置 (0-35分): 价格 vs MA20/MA50
    - RSI (0-40分): 超卖高分
    - 区间位置 (0-25分): 30日低点附近高分
    """
    score = 0
    details = []
    
    # 均线位置 (35分)
    if price > ma20:
        ma_score = 35
        details.append(f"站上MA20(+35)")
    elif price > ma50:
        ma_score = 22
        details.append(f"高于MA50但低于MA20(+22)")
    elif ma50 > ma20:
        # 均线空头排列
        discount = (ma50 - price) / (ma50 - ma20) * 15
        ma_score = max(0, 10 - discount)
        details.append(f"低于双均线且空头排列(+{ma_score:.0f})")
    else:
        ma_score = 12
        details.append(f"低于双均线(+12)")
    score += ma_score
    
    # RSI (40分) - 超卖高分
    if rsi < 25:
        rsi_score = 40
        details.append(f"RSI严重超卖({rsi:.0f})(+40)")
    elif rsi < 30:
        rsi_score = 35
        details.append(f"RSI超卖({rsi:.0f})(+35)")
    elif rsi < 40:
        rsi_score = 28
        details.append(f"RSI偏低({rsi:.0f})(+28)")
    elif rsi > 80:
        rsi_score = 0
        details.append(f"RSI严重超买({rsi:.0f})(+0)")
    elif rsi > 70:
        rsi_score = 10
        details.append(f"RSI超买({rsi:.0f})(+10)")
    elif rsi > 60:
        rsi_score = 20
        details.append(f"RSI偏高({rsi:.0f})(+20)")
    else:
        rsi_score = 20
        details.append(f"RSI中性({rsi:.0f})(+20)")
    score += rsi_score
    
    # 区间位置 (25分)
    if high_30d > low_30d:
        range_pos = (price - low_30d) / (high_30d - low_30d)
    else:
        range_pos = 0.5
    
    if range_pos < 0.2:
        range_score = 25
        details.append(f"接近30日低点({range_pos*100:.0f}%)，严重低估(+25)")
    elif range_pos < 0.35:
        range_score = 20
        details.append(f"低于区间35%({range_pos*100:.0f}%)，偏低(+20)")
    elif range_pos < 0.5:
        range_score = 15
        details.append(f"区间下半({range_pos*100:.0f}%)(+15)")
    elif range_pos < 0.75:
        range_score = 10
        details.append(f"区间上半({range_pos*100:.0f}%)(+10)")
    else:
        range_score = 3
        details.append(f"接近30日高点({range_pos*100:.0f}%)，偏高(+3)")
    score += range_score
    
    return {
        "score": min(100, max(0, score)),
        "details": details
    }


# ==================== 2. 原油/通胀评分 ====================

def score_oil(oil_price: float) -> dict:
    """
    原油评分 (0-100)
    
    逻辑: 原油涨 → 通胀预期涨 → 黄金受益
    
    评分规则:
    - >110: 100分 (恶性通胀)
    - 100-110: 90分 (高通胀)
    - 80-100: 75分 (通胀压力)
    - 70-80: 60分 (中高油价)
    - 50-70: 50分 (中性)
    - 30-50: 35分 (低通胀/通缩风险)
    - <30: 20分 (通缩)
    """
    if oil_price is None:
        return {"score": 50, "details": ["原油数据获取失败(+50)"]}
    
    if oil_price > 110:
        score = 100
        details = [f"原油${oil_price:.0f}>110 恶性通胀预期(+100)"]
    elif oil_price > 100:
        score = 90
        details = [f"原油${oil_price:.0f}>100 高通胀(+90)"]
    elif oil_price > 80:
        score = 75
        details = [f"原油${oil_price:.0f}>80 通胀压力(+75)"]
    elif oil_price > 70:
        score = 60
        details = [f"原油${oil_price:.0f}>70 中高油价(+60)"]
    elif oil_price > 50:
        score = 50
        details = [f"原油${oil_price:.0f} 中性区间(+50)"]
    elif oil_price > 30:
        score = 35
        details = [f"原油${oil_price:.0f}<50 低通胀/通缩风险(+35)"]
    else:
        score = 20
        details = [f"原油${oil_price:.0f}<30 通缩风险(+20)"]
    
    return {"score": score, "details": details}


# ==================== 3. 避险情绪评分 ====================

def score_risk_sentiment(
    geo_events: list,
    vix: float,
    dxy: float,
    btc_change_7d: float,
    us10y_change: float,
    credit_spread: float
) -> dict:
    """
    避险情绪评分 (0-100, 越高表示避险情绪越强)
    
    子因素:
    1. 地缘政治 G (25%): 战争/冲突/制裁
    2. VIX恐慌指数 (20%): >20恐慌, <15平静
    3. 美元指数 DXY (15%): >105强美元利空, <95弱美元利好
    4. 加密货币 (15%): BTC跌=避险, BTC涨=风险偏好
    5. 美债收益率 (15%): 收益率跌=避险买债=利好黄金
    6. 信用利差 (10%): 利差扩大=恐慌
    """
    sub_scores = {}
    details = []
    
    # 1. 地缘政治 (25%)
    geo_score = score_geopolitical(geo_events)
    sub_scores["geopolitical"] = geo_score["score"]
    details.extend([f"G: {d}" for d in geo_score["details"]])
    
    # 2. VIX (20%)
    vix_score = score_vix(vix)
    sub_scores["vix"] = vix_score["score"]
    details.extend(vix_score["details"])
    
    # 3. 美元指数 (15%)
    dxy_score = score_dxy(dxy)
    sub_scores["dxy"] = dxy_score["score"]
    details.extend(dxy_score["details"])
    
    # 4. 加密货币 (15%)
    crypto_score = score_crypto(btc_change_7d)
    sub_scores["crypto"] = crypto_score["score"]
    details.extend(crypto_score["details"])
    
    # 5. 美债收益率 (15%)
    bond_score = score_bond_yield(us10y_change)
    sub_scores["bond_yield"] = bond_score["score"]
    details.extend(bond_score["details"])
    
    # 6. 信用利差 (10%)
    spread_score = score_credit_spread(credit_spread)
    sub_scores["credit_spread"] = spread_score["score"]
    details.extend(spread_score["details"])
    
    # 加权计算
    total = sum(sub_scores[k] * RISK_SUBSCORE_WEIGHTS[k] for k in RISK_SUBSCORE_WEIGHTS)
    
    return {
        "score": min(100, max(0, total)),
        "sub_scores": sub_scores,
        "details": details
    }


def score_geopolitical(geo_events: list) -> dict:
    """
    地缘政治评分 (0-100)
    
    无事件: 50分 (基准)
    有事件: 事件最高分 (不叠加，避免重复计算)
    
    高权重事件:
    - 中东战争/以色列-伊朗: +50
    - 俄乌战争升级/北约直接介入: +50
    - 台海军事冲突: +50
    - 中国攻台/美国介入: +50 (最高)
    
    中权重事件:
    - 美中贸易战升级/新关税: +30
    - 朝鲜半岛冲突: +30
    - 伊朗核危机: +30
    - 欧洲能源危机: +25
    
    低权重事件:
    - 俄罗斯被制裁: +15
    - 其他地区冲突: +15
    - 英国退欧余波: +10
    """
    if not geo_events:
        return {"score": 50, "details": ["无重大地缘政治事件(+50)"]}
    
    events_score = {
        # 最高权重
        "中东战争": 50, "以色列伊朗": 50, "以伊冲突": 50, "伊朗以色列": 50,
        "台海": 50, "中国攻台": 50, "台湾战争": 50, "中国台湾": 50,
        "俄乌升级": 50, "北约介入": 50, "俄罗斯北约": 50,
        
        # 中权重
        "贸易战": 30, "关税": 30, "美中": 30, "中美": 30,
        "朝鲜": 30, "朝鲜半岛": 30, "朝鲜导弹": 30,
        "伊朗核": 30, "伊朗制裁": 25,
        "欧洲能源": 25, "俄罗斯断气": 25,
        
        # 低权重
        "俄罗斯制裁": 15, "俄罗斯": 10,
        "英国退欧": 10, "英国": 5,
        "欧盟": 5, "德国": 5, "法国": 5,
    }
    
    max_score = 50
    matched_events = []
    
    for event in geo_events:
        event_upper = str(event).upper()
        for keywords, score in events_score.items():
            if keywords.upper() in event_upper:
                if score > max_score:
                    max_score = score
                matched_events.append(f"{event}(+{score})")
                break
    
    if matched_events:
        return {
            "score": min(100, 50 + max_score),
            "details": matched_events
        }
    
    return {"score": 50, "details": ["地缘政治事件未识别(+50)"]}


def score_vix(vix: float) -> dict:
    """
    VIX恐慌指数评分 (0-100)
    
    - >50: 100分 (金融危机的恐慌)
    - 40-50: 90分 (极度恐慌)
    - 30-40: 75分 (高度恐慌)
    - 25-30: 60分 (明显焦虑)
    - 20-25: 50分 (轻度恐慌)
    - 15-20: 40分 (正常波动)
    - 10-15: 30分 (极度平静)
    - <10: 20分 (异常平静，可能反转)
    """
    if vix is None:
        return {"score": 40, "details": ["VIX数据获取失败(+40)"]}
    
    if vix > 50:
        score = 100
        details = [f"VIX>{vix:.0f} 金融危机级别(+100)"]
    elif vix > 40:
        score = 90
        details = [f"VIX>{vix:.0f} 极度恐慌(+90)"]
    elif vix > 30:
        score = 75
        details = [f"VIX>{vix:.0f} 高度恐慌(+75)"]
    elif vix > 25:
        score = 60
        details = [f"VIX>{vix:.0f} 明显焦虑(+60)"]
    elif vix > 20:
        score = 50
        details = [f"VIX={vix:.0f} 轻度恐慌(+50)"]
    elif vix > 15:
        score = 40
        details = [f"VIX={vix:.0f} 正常区间(+40)"]
    elif vix > 10:
        score = 30
        details = [f"VIX={vix:.0f} 极度平静(+30)"]
    else:
        score = 20
        details = [f"VIX={vix:.0f} 异常平静(+20)"]
    
    return {"score": score, "details": details}


def score_dxy(dxy: float) -> dict:
    """
    美元指数评分 (0-100)
    
    逻辑: 弱美元 → 黄金相对升值 + 以美元计价商品受益
    
    - <85: 100分 (极弱美元，利好黄金)
    - 85-90: 80分 (弱美元)
    - 90-95: 65分 (偏弱)
    - 95-100: 50分 (中性)
    - 100-105: 35分 (偏强，利空黄金)
    - 105-110: 20分 (强美元)
    - >110: 5分 (极强美元)
    """
    if dxy is None:
        return {"score": 50, "details": ["美元指数获取失败(+50)"]}
    
    if dxy < 85:
        score = 100
        details = [f"美元{dxy:.1f}<85 极弱美元(+100)"]
    elif dxy < 90:
        score = 80
        details = [f"美元{dxy:.1f}<90 弱美元(+80)"]
    elif dxy < 95:
        score = 65
        details = [f"美元{dxy:.1f}<95 偏弱(+65)"]
    elif dxy < 100:
        score = 50
        details = [f"美元{dxy:.1f}<100 中性区间(+50)"]
    elif dxy < 105:
        score = 35
        details = [f"美元{dxy:.1f}>100 偏强(-15)"]
    elif dxy < 110:
        score = 20
        details = [f"美元{dxy:.1f}>105 强美元(-30)"]
    else:
        score = 5
        details = [f"美元{dxy:.1f}>110 极强美元(-45)"]
    
    return {"score": score, "details": details}


def score_crypto(btc_change_7d: float) -> dict:
    """
    加密货币评分 (0-100)
    
    逻辑: BTC大跌 → 避险情绪升温 → 利好黄金
          BTC大涨 → 风险偏好强 → 利空黄金
    
    - 7日跌>25%: 100分 (强烈避险)
    - 7日跌>15%: 80分
    - 7日跌>10%: 65分
    - 7日跌>5%: 55分
    - 7日涨跌±5%: 50分 (中性)
    - 7日涨>5%: 40分
    - 7日涨>10%: 25分
    - 7日涨>20%: 10分
    - 7日涨>30%: 0分 (极度风险偏好)
    """
    if btc_change_7d is None:
        return {"score": 50, "details": ["BTC数据获取失败(+50)"]}
    
    change = btc_change_7d
    
    if change < -25:
        score = 100
        details = [f"BTC 7日{change:.0f}% 强烈避险(+100)"]
    elif change < -15:
        score = 80
        details = [f"BTC 7日{change:.0f}% 明显避险(+80)"]
    elif change < -10:
        score = 65
        details = [f"BTC 7日{change:.0f}% 偏弱避险(+65)"]
    elif change < -5:
        score = 55
        details = [f"BTC 7日{change:.0f}% 轻微避险(+55)"]
    elif change < 5:
        score = 50
        details = [f"BTC 7日{change:+.0f}% 中性区间(+50)"]
    elif change < 10:
        score = 40
        details = [f"BTC 7日{change:.0f}% 风险偏好(-10)"]
    elif change < 20:
        score = 25
        details = [f"BTC 7日{change:.0f}% 强风险偏好(-25)"]
    elif change < 30:
        score = 10
        details = [f"BTC 7日{change:.0f}% 极强风险偏好(-40)"]
    else:
        score = 0
        details = [f"BTC 7日{change:.0f}% 狂热风险偏好(-50)"]
    
    return {"score": score, "details": details}


def score_bond_yield(us10y_change: float) -> dict:
    """
    美债收益率变化评分 (0-100)
    
    逻辑: 收益率下跌 → 资金流向债券/黄金避险
          收益率上涨 → 风险偏好上升 → 黄金承压
    
    10年期收益率变化 (与30日前比较):
    - 跌>50bp: 100分 (经济衰退信号，强烈避险)
    - 跌30-50bp: 85分
    - 跌20-30bp: 70分
    - 跌10-20bp: 60分
    - 跌<10bp: 55分
    - 变化±5bp: 50分 (中性)
    - 涨10-20bp: 35分
    - 涨20-30bp: 20分
    - 涨>30bp: 5分 (风险偏好强)
    """
    if us10y_change is None:
        return {"score": 50, "details": ["美债数据获取失败(+50)"]}
    
    change = us10y_change  # basis points
    
    if change < -50:
        score = 100
        details = [f"美债收益率{change:+.0f}bp 衰退信号(+100)"]
    elif change < -30:
        score = 85
        details = [f"美债收益率{change:+.0f}bp 经济放缓(+85)"]
    elif change < -20:
        score = 70
        details = [f"美债收益率{change:+.0f}bp 避险升温(+70)"]
    elif change < -10:
        score = 60
        details = [f"美债收益率{change:+.0f}bp 偏多(+60)"]
    elif change < 10:
        score = 50
        details = [f"美债收益率{change:+.0f}bp 中性(+50)"]
    elif change < 20:
        score = 35
        details = [f"美债收益率{change:+.0f}bp 风险偏好(-15)"]
    elif change < 30:
        score = 20
        details = [f"美债收益率{change:+.0f}bp 强风险偏好(-30)"]
    else:
        score = 5
        details = [f"美债收益率{change:+.0f}bp 极度乐观(-45)"]
    
    return {"score": score, "details": details}


def score_credit_spread(spread: float) -> dict:
    """
    信用利差评分 (0-100)
    
    逻辑: 利差扩大 → 企业违约风险上升 → 经济担忧 → 避险
    
    美国高收益债券(HY) vs 投资级(IG)利差:
    - >1000bp: 100分 (金融危机)
    - 800-1000bp: 80分 (严重担忧)
    - 600-800bp: 60分 (明显压力)
    - 400-600bp: 50分 (正常区间)
    - 300-400bp: 40分 (偏低，乐观)
    - <300bp: 25分 (异常低，极度乐观)
    """
    if spread is None:
        return {"score": 50, "details": ["信用利差数据获取失败(+50)"]}
    
    if spread > 1000:
        score = 100
        details = [f"信用利差{spread:.0f}bp>1000 金融危机(+100)"]
    elif spread > 800:
        score = 80
        details = [f"信用利差{spread:.0f}bp>800 严重担忧(+80)"]
    elif spread > 600:
        score = 60
        details = [f"信用利差{spread:.0f}bp>600 明显压力(+60)"]
    elif spread > 400:
        score = 50
        details = [f"信用利差{spread:.0f}bp 正常区间(+50)"]
    elif spread > 300:
        score = 40
        details = [f"信用利差{spread:.0f}bp<400 偏低乐观(+40)"]
    else:
        score = 25
        details = [f"信用利差{spread:.0f}bp<300 极度乐观(+25)"]
    
    return {"score": score, "details": details}


# ==================== 主计算函数 ====================

def calculate_final_score(tech: dict, oil: dict, risk: dict) -> dict:
    """
    综合评分计算
    
    公式:
    S = 0.25·T + 0.20·O + 0.55·R
    """
    
    raw_score = (
        WEIGHTS["technical"] * tech["score"] +
        WEIGHTS["oil"] * oil["score"] +
        WEIGHTS["risk_sentiment"] * risk["score"]
    )
    
    final_score = max(0, min(100, raw_score))
    
    # 信号评级
    if final_score >= 80:
        rating = "🟢 强烈买入"
        signal = "STRONG_BUY"
        action = "积极建仓，分批买入"
    elif final_score >= 65:
        rating = "🟡 买入"
        signal = "BUY"
        action = "可考虑买入，止损35,000"
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
        action = "清仓，等待低位"
    
    return {
        "final_score": final_score,
        "rating": rating,
        "signal": signal,
        "action": action,
    }


# ==================== 数据获取 ====================

def get_market_data() -> dict:
    """获取所有市场数据"""
    data = {}
    
    # 黄金 + 技术指标
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
        pass
    
    # VIX
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1d")
        if not hist.empty:
            data["vix"] = hist['Close'].iloc[-1]
    except:
        pass
    
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
        pass
    
    # 美债收益率
    try:
        bond = yf.Ticker("^TNX")  # 10年期国债收益率
        hist = bond.history(period="1mo")
        if not hist.empty and len(hist) >= 20:
            data["us10y_now"] = bond.info.get("regularMarketPrice", hist['Close'].iloc[-1])
            data["us10y_30d_ago"] = hist['Close'].iloc[-20]
            data["us10y_change"] = (data["us10y_now"] - data["us10y_30d_ago"]) * 100  # 转为bp
    except:
        try:
            # 备用：用TLT ETF反推
            tlt = yf.Ticker("TLT")
            hist_now = tlt.history(period="1d")
            hist_30d = tlt.history(period="1mo")
            if not hist_now.empty and not hist_30d.empty and len(hist_30d) >= 20:
                # 债券收益率和价格反向
                price_change = (hist_now['Close'].iloc[-1] / hist_30d['Close'].iloc[-20] - 1) * 100
                data["us10y_change"] = -price_change * 10  # 粗略估算
        except:
            pass
    
    # 信用利差 (HYG vs LQD ETF利差)
    # 通常高收益债收益率比投资级高约3-5%，即300-500bp是正常
    try:
        hyg = yf.Ticker("HYG")  # 高收益债ETF
        lqd = yf.Ticker("LQD")  # 投资级债ETF
        hyg_hist = hyg.history(period="1d")
        lqd_hist = lqd.history(period="1d")
        if not hyg_hist.empty and not lqd_hist.empty:
            # 用价格反推收益率（简化估算）
            # 债券价格和收益率反向
            hyg_price = hyg_hist['Close'].iloc[-1]
            lqd_price = lqd_hist['Close'].iloc[-1]
            # 粗略：假设10年期，久期≈10，收益率≈(100-价格)/10
            hyg_yield_est = max(0, (100 - hyg_price) / 10)
            lqd_yield_est = max(0, (100 - lqd_price) / 10)
            data["credit_spread"] = (hyg_yield_est - lqd_yield_est) * 100  # 转为bp
    except:
        # 备用：使用默认正常值
        data["credit_spread"] = 350  # 正常区间约350bp
    
    return data


def fetch_geopolitical_news() -> list:
    """
    获取地缘政治新闻
    目前返回预设关键词，后续接入News API
    """
    # TODO: 接入 Finnhub News API 或 Bing News API
    # Finnhub token: d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g
    
    # 预设关键词（根据当前世界局势）
    known_events = [
        "俄乌战争", "俄罗斯乌克兰", "北约东扩",
        "中东战争", "以色列加沙", "伊朗以色列",
        "美中贸易战", "中美关税", "科技战",
        "台海局势", "台湾", "解放军",
        "朝鲜导弹", "朝鲜核试验",
    ]
    
    # 这里后续接入API自动抓取
    # 暂时返回空列表，人工判断
    return []


# ==================== 主程序 ====================

def run_analysis(geo_events: list = None):
    """运行完整分析"""
    
    print("=" * 70)
    print("🌟 黄金综合评分公式 v2")
    print("=" * 70)
    print(f"""
公式: S = w₁·T + w₂·O + w₃·R

权重:
  T (技术面)    = 25%
  O (原油)     = 20%  
  R (避险情绪) = 55%
       └─ 地缘政治 G = 25%
       └─ VIX恐慌   = 20%
       └─ 美元指数  = 15%
       └─ 加密货币  = 15%
       └─ 美债收益  = 15%
       └─ 信用利差  = 10%
""")
    
    # 获取数据
    data = get_market_data()
    
    # 获取地缘政治事件
    if geo_events is None:
        geo_events = fetch_geopolitical_news()
    
    # 打印市场数据
    print("=" * 70)
    print("📊 市场数据")
    print("=" * 70)
    gp = f"HK${data.get('gold_price', 0):.0f}" if data.get('gold_price') else "N/A"
    ma20 = f"HK${data.get('ma20', 0):.0f}" if data.get('ma20') else "N/A"
    rsi = f"{data.get('rsi', 0):.1f}" if data.get('rsi') else "N/A"
    lo30 = f"{data.get('low_30d', 0):.0f}" if data.get('low_30d') else "N/A"
    hi30 = f"{data.get('high_30d', 0):.0f}" if data.get('high_30d') else "N/A"
    oil = f"${data.get('oil_price', 0):.2f}" if data.get('oil_price') else "N/A"
    vix = f"{data.get('vix', 0):.1f}" if data.get('vix') else "N/A"
    dxy = f"{data.get('dxy', 0):.1f}" if data.get('dxy') else "N/A"
    btc = f"{data.get('btc_change_7d', 0):+.1f}%" if data.get('btc_change_7d') else "N/A"
    bond = f"{data.get('us10y_change', 0):+.0f}bp" if data.get('us10y_change') else "N/A"
    spread = f"{data.get('credit_spread', 0):.0f}bp" if data.get('credit_spread') else "N/A"
    
    print(f"   金价: {gp}")
    print(f"   MA20: {ma20}")
    print(f"   RSI(14): {rsi}")
    print(f"   30日区间: {lo30} - {hi30}")
    print(f"   ────────────")
    print(f"   原油: {oil}")
    print(f"   VIX恐慌: {vix}")
    print(f"   美元指数: {dxy}")
    print(f"   BTC 7日: {btc}")
    print(f"   美债收益30日: {bond}")
    print(f"   信用利差: {spread}")
    
    # 计算各项得分
    tech = score_technical(
        price=data.get("gold_price", 0),
        ma20=data.get("ma20", 0),
        ma50=data.get("ma50", 0),
        rsi=data.get("rsi", 50),
        low_30d=data.get("low_30d", 0),
        high_30d=data.get("high_30d", 0)
    )
    
    oil = score_oil(data.get("oil_price"))
    risk = score_risk_sentiment(
        geo_events=geo_events,
        vix=data.get("vix"),
        dxy=data.get("dxy"),
        btc_change_7d=data.get("btc_change_7d"),
        us10y_change=data.get("us10y_change"),
        credit_spread=data.get("credit_spread")
    )
    
    # 计算最终评分
    result = calculate_final_score(tech, oil, risk)
    
    # 打印各项评分
    print("=" * 70)
    print("📈 各因素评分")
    print("=" * 70)
    
    print(f"\n1️⃣ 技术面 (T): {tech['score']:.0f}/100")
    for detail in tech['details']:
        print(f"   {detail}")
    
    print(f"\n2️⃣ 原油/通胀 (O): {oil['score']:.0f}/100")
    for detail in oil['details']:
        print(f"   {detail}")
    
    print(f"\n3️⃣ 避险情绪 (R): {risk['score']:.0f}/100")
    print(f"   子因素:")
    sub_names = {
        "geopolitical": "地缘政治",
        "vix": "VIX恐慌",
        "dxy": "美元指数",
        "crypto": "加密货币",
        "bond_yield": "美债收益",
        "credit_spread": "信用利差"
    }
    for k, w in RISK_SUBSCORE_WEIGHTS.items():
        sub_score = risk['sub_scores'].get(k, 0)
        print(f"   - {sub_names.get(k, k)}: {sub_score:.0f} × {w*100:.0f}% = {sub_score*w:.1f}")
    for detail in risk['details']:
        print(f"   {detail}")
    
    print()
    print("=" * 70)
    print("🏆 综合评分")
    print("=" * 70)
    
    print(f"\n   S = 0.25×{tech['score']:.0f} + 0.20×{oil['score']:.0f} + 0.55×{risk['score']:.0f}")
    print(f"   S = {result['final_score']:.1f}")
    print(f"\n   评级: {result['rating']}")
    print(f"   信号: {result['signal']}")
    print(f"\n   💰 操作建议: {result['action']}")
    
    print()
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="黄金综合评分")
    parser.add_argument("--geo", nargs="+", help="地缘政治事件（可选）")
    args = parser.parse_args()
    
    geo_events = args.geo if args.geo else None
    result = run_analysis(geo_events)
    
    print("\n📋 JSON输出:")
    print(json.dumps({
        "score": result["final_score"],
        "rating": result["rating"],
        "signal": result["signal"],
        "action": result["action"],
    }, ensure_ascii=False, indent=2))
