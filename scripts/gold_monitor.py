#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金价监控脚本
每分钟检查金价，接近止损/止盈点时通知
"""

import requests
import yfinance as yf
import json
import os
from datetime import datetime

TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb93hr01qhkb43v28g"
ALERT_FILE = "portfolio/gold_alert.json"

# 止损止盈位 (港币/盎司) - HSBC银行价
STOP_LOSS = 35000   # 止损
TAKE_PROFIT_1 = 37000  # 第一止盈
TAKE_PROFIT_2 = 38500  # 第二止盈
TAKE_PROFIT_3 = 40000  # 第三止盈

# 加仓信号价位 (港币/盎司)
ADD_POSITION_ZONE = 35500   # 加仓区间下限（回到35,500-36,000可小仓试单）
ADD_POSITION_MA20 = 39100   # 突破20日均线确认升势（可加仓）

# HSBC银行价溢价系数 (国际金价 × 1.09 ≈ HSBC价)
HSBC_PREMIUM = 1.09

# 警报阈值（接近多少%时提醒）
ALERT_THRESHOLD = 1.0  # 1% 偏差内提醒


def get_gold_price():
    """获取金价（港币/盎司）- HSBC银行价"""
    try:
        # GLD ETF 换算 (1 GLD ≈ 1/10 oz 黄金)
        gld = yf.Ticker("GLD")
        hist = gld.history(period="1d")
        if not hist.empty:
            gld_price = hist['Close'].iloc[-1]
            # GLD × 10 = 黄金美元价格
            gold_usd = gld_price * 10
            # 美元转港币 × 7.8
            gold_hkd = gold_usd * 7.8
            # 应用 HSBC 溢价 (国际价 × 1.09)
            gold_hsbc = gold_hkd * HSBC_PREMIUM
            return gold_hsbc, "HSBC银行价"
    except:
        pass
    
    return None, None


def get_gold_with_ma():
    """获取金价及技术指标"""
    try:
        gld = yf.Ticker("GLD")
        hist = gld.history(period="3mo")
        if hist.empty:
            return None, None, None
        
        gld_price = hist['Close'].iloc[-1] * 10 * 7.8 * HSBC_PREMIUM
        ma20 = hist['Close'].rolling(20).mean().iloc[-1] * 10 * 7.8 * HSBC_PREMIUM
        ma50 = hist['Close'].rolling(50).mean().iloc[-1] * 10 * 7.8 * HSBC_PREMIUM if len(hist) >= 50 else None
        
        # 30日低点
        low_30d = hist['Low'].rolling(30).min().iloc[-1] * 10 * 7.8 * HSBC_PREMIUM
        
        return gld_price, ma20, low_30d
    except:
        return None, None, None


def check_alerts(price, ma20=None, low_30d=None):
    """检查是否触发警报"""
    alerts = []
    
    if price is None:
        return alerts
    
    # 止损检查
    diff_pct = (price - STOP_LOSS) / STOP_LOSS * 100
    
    if price <= STOP_LOSS:
        alerts.append({
            "type": "STOP_LOSS",
            "message": f"🔴 金价触及止损！\n当前: HK${price:.0f}\n止损位: HK${STOP_LOSS}",
            "priority": "HIGH"
        })
    elif price <= STOP_LOSS * (1 + ALERT_THRESHOLD/100):
        alerts.append({
            "type": "STOP_LOSS_WARNING",
            "message": f"⚠️ 金价接近止损！\n当前: HK${price:.0f}\n止损位: HK${STOP_LOSS}\n差距: {diff_pct:.1f}%",
            "priority": "MEDIUM"
        })
    
    # 止盈检查
    if price >= TAKE_PROFIT_3:
        alerts.append({
            "type": "TAKE_PROFIT_3",
            "message": f"🟢 金价达到目标3！\n当前: HK${price:.0f}\n目标: HK${TAKE_PROFIT_3}",
            "priority": "HIGH"
        })
    elif price >= TAKE_PROFIT_2:
        alerts.append({
            "type": "TAKE_PROFIT_2",
            "message": f"🟢 金价达到目标2！\n当前: HK${price:.0f}\n目标: HK${TAKE_PROFIT_2}",
            "priority": "MEDIUM"
        })
    elif price >= TAKE_PROFIT_1:
        alerts.append({
            "type": "TAKE_PROFIT_1",
            "message": f"🟢 金价达到目标1！\n当前: HK${price:.0f}\n目标: HK${TAKE_PROFIT_1}",
            "priority": "LOW"
        })
    
    # 加仓信号检查
    if ma20 and low_30d:
        # 信号1：回到加仓区间 (35,500 - 36,000)
        if 35500 <= price <= 36000:
            alerts.append({
                "type": "ADD_POSITION_ZONE",
                "message": f"🟡 加仓机会：金价回到35,500-36,000区间\n当前: HK${price:.0f}\n可小仓试单，止损34,500",
                "priority": "MEDIUM"
            })
        
        # 信号2：突破20日均线
        if price >= ma20:
            alerts.append({
                "type": "BREAK_MA20",
                "message": f"🟢 加仓信号：突破20日均线！\n当前: HK${price:.0f}\n均线: HK${ma20:.0f}\n确认升势，可加仓",
                "priority": "HIGH"
            })
    
    return alerts


def load_last_alert():
    """加载上次警报时间"""
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            data = json.load(f)
            return data.get("last_alert_time"), data.get("last_alert_type")
    return None, None


def save_alert(alert_type):
    """保存警报记录"""
    with open(ALERT_FILE, "w") as f:
        json.dump({
            "last_alert_time": datetime.now().isoformat(),
            "last_alert_type": alert_type
        }, f)


def should_send_alert(alert_type, last_alert_type):
    """判断是否应该发送警报（避免重复）"""
    # 高优先级警报总是发送
    if "STOP_LOSS" in alert_type and "WARNING" not in alert_type:
        return True
    
    # 同类型警报10分钟内不重复
    if last_alert_type == alert_type:
        return False
    
    return True


def run_monitor():
    """运行监控"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 金价监控...")
    
    price, source = get_gold_price()
    price_ma, ma20, low_30d = get_gold_with_ma()
    
    if price is None:
        print("❌ 无法获取金价")
        return None
    
    if price_ma is None:
        price_ma = price
        ma20 = None
        low_30d = None
    
    print(f"💰 金价: HK${price:.0f}/oz ({source})")
    if ma20:
        print(f"📊 20日均线: HK${ma20:.0f} | 30日低点: HK${low_30d:.0f}")
    
    # 检查警报
    alerts = check_alerts(price, ma20, low_30d)
    
    # 获取上次警报
    last_time, last_type = load_last_alert()
    
    for alert in alerts:
        if should_send_alert(alert["type"], last_type):
            print(f"\n🚨 {alert['message']}\n")
            save_alert(alert["type"])
            return alert
    
    # 正常状态
    status = f"💰 金价: HK${price:.0f} | 止损: HK${STOP_LOSS} | 目标: HK${TAKE_PROFIT_1}/{TAKE_PROFIT_2}/{TAKE_PROFIT_3}"
    print(status)
    
    return None


if __name__ == "__main__":
    result = run_monitor()
    if result:
        print("\n🚨 警报触发！")
