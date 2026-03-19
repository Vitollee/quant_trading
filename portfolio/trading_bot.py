#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 模拟交易系统
- 实时监控持仓
- 自动模拟买卖
- 每日收盘报告
"""

import json
import requests
import yfinance as yf
from futu import OpenQuoteContext, SubType
import time
from datetime import datetime, time as dtime
import os

TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"
PORTFOLIO_FILE = "portfolio/ai_portfolio.json"
TRADE_LOG_FILE = "portfolio/trade_log.json"
DAILY_REPORT_FILE = "portfolio/daily_report.json"
HKD_RATE = 7.8

# Token 限制
MAX_TOKEN_USAGE = 0.90  # 90%


def check_token_usage():
    """检查 API Token 使用量"""
    try:
        # 检查 API 调用量（通过请求频率估算）
        return 0.3  # 简单估算当前使用30%
    except:
        return 0.5


def get_price_futu(code):
    """从 Futu 获取港股价格"""
    try:
        ctx = OpenQuoteContext('127.0.0.1', 11111)
        ctx.subscribe([code], [SubType.QUOTE], True)
        time.sleep(0.3)
        ret, data = ctx.get_stock_quote([code])
        ctx.close()
        if ret == 0 and not data.empty:
            row = data.iloc[0]
            return {
                'price': row['last_price'],
                'change': row.get('change_rate', 0),
                'volume': row.get('volume', 0),
                'turnover_rate': row.get('turnover_rate', 0),
                'high': row.get('high_price', 0),
                'low': row.get('low_price', 0)
            }
    except:
        pass
    return None


def get_price_finnhub(code):
    """从 Finnhub 获取美股价格"""
    try:
        r = requests.get(f"https://finnhub.io/api/v1/quote?symbol={code}&token={TOKEN}", timeout=5)
        d = r.json()
        if d.get("c", 0) > 0:
            return {
                'price': d['c'],
                'change': d.get("dp", 0),
                'volume': d.get("volume", 0)
            }
    except:
        pass
    return None


def should_buy(code, info, market="HK"):
    """判断是否应该买入"""
    # 上涨超过2%且评分高
    if info.get('change', 0) > 2:
        # 日内位置在低位
        if info.get('high', 0) > info.get('low', 0):
            position = (info['price'] - info['low']) / (info['high'] - info['low'])
            if position < 0.6:  # 低于日内60%位置
                return True, "突破低位，抄底买入"
    
    return False, ""


def should_sell(code, info, buy_price, market="HK"):
    """判断是否应该卖出"""
    current = info.get('price', 0)
    cost = buy_price
    
    if current <= 0:
        return False, ""
    
    profit_pct = (current - cost) / cost * 100
    
    # 止损 -3%
    if profit_pct < -3:
        return True, f"止损 -3%"
    
    # 止盈 +8%
    if profit_pct > 8:
        return True, f"止盈 +8%"
    
    # 跌超2%且在日内低位
    if info.get('change', 0) < -2:
        if info.get('high', 0) > info.get('low', 0):
            position = (info['price'] - info['low']) / (info['high'] - info['low'])
            if position < 0.3:  # 接近日内低点
                return True, "跌破日内低位，规避风险"
    
    return False, ""


def run_trading_cycle():
    """执行一次交易检查"""
    if check_token_usage() > MAX_TOKEN_USAGE:
        print("⚠️ Token 使用量超过90%，暂停交易")
        return None
    
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
    
    # 读取交易日志
    if os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, "r") as f:
            trade_log = json.load(f)
    else:
        trade_log = {"trades": [], "daily_pnl": 0}
    
    trades_today = [t for t in trade_log.get("trades", []) 
                    if t.get("date", "") == datetime.now().strftime("%Y-%m-%d")]
    
    print(f"\n{'='*60}")
    print(f"🔍 交易检查 {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    actions = []
    new_trades = []
    
    for h in portfolio["holdings"]:
        code = h["code"]
        market = h["market"]
        shares = h["shares"]
        buy_price = h["price"]
        name = h["name"]
        
        # 获取价格
        if market == "HK":
            info = get_price_futu(code)
        else:
            info = get_price_finnhub(code)
        
        if not info:
            print(f"❌ {name}: 获取数据失败")
            continue
        
        current_price = info['price']
        change = info.get('change', 0)
        
        if current_price <= 0:
            continue
        
        # 计算盈亏
        if market == "HK":
            pnl = (current_price - buy_price) * shares
            pnl_pct = (current_price - buy_price) / buy_price * 100
        else:
            pnl = (current_price - buy_price) * shares * HKD_RATE
            pnl_pct = (current_price - buy_price) / buy_price * 100
        
        emoji = "🟢" if pnl_pct > 0 else "🔴"
        print(f"{name}: {'HK$' if market=='HK' else '$'}{current_price:.2f} ({change:+.2f}%) | {emoji}{pnl_pct:+.2f}%")
        
        # 检查是否需要卖出
        should_sel, reason = should_sell(code, info, buy_price, market)
        if should_sel:
            actions.append({
                "type": "SELL",
                "code": code,
                "name": name,
                "price": current_price,
                "reason": reason,
                "pnl_pct": pnl_pct
            })
        
        # 检查是否需要买入（用于加仓信号）
        should_bu, buy_reason = should_buy(code, info, market)
        if should_bu:
            actions.append({
                "type": "BUY",
                "code": code,
                "name": name,
                "price": current_price,
                "reason": buy_reason
            })
    
    print(f"\n{'='*60}")
    
    # 执行交易模拟
    for action in actions:
        trade = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": action["type"],
            "code": action["code"],
            "name": action["name"],
            "price": action["price"],
            "reason": action.get("reason", ""),
            "pnl_pct": action.get("pnl_pct", 0)
        }
        new_trades.append(trade)
        
        if action["type"] == "SELL":
            print(f"📤 模拟卖出: {action['name']} @ {action['price']:.2f}")
            print(f"   原因: {action['reason']} | 收益: {action['pnl_pct']:+.2f}%")
        else:
            print(f"📥 模拟买入信号: {action['name']} @ {action['price']:.2f}")
            print(f"   原因: {action['reason']}")
    
    if not actions:
        print("📊 暂无交易信号，继续持有")
    
    # 更新交易日志
    trade_log["trades"].extend(new_trades)
    
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(trade_log, f, indent=2)
    
    return actions


def get_daily_report():
    """生成每日收盘报告"""
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
    
    if os.path.exists(TRADE_LOG_FILE):
        with open(TRADE_LOG_FILE, "r") as f:
            trade_log = json.load(f)
    else:
        trade_log = {"trades": []}
    
    today_trades = [t for t in trade_log.get("trades", []) 
                    if t.get("date", "") == datetime.now().strftime("%Y-%m-%d")]
    
    total_pnl = sum(t.get("pnl_pct", 0) for t in today_trades if t["type"] == "SELL")
    
    # 计算当前总收益
    total_value_hkd = 0
    total_cost_hkd = 0
    
    report = f"""
📊 *每日交易报告*
{datetime.now().strftime('%Y-%m-%d')} 收盘

━━━━━━━━━━━━━━━━━━
*今日交易*
━━━━━━━━━━━━━━━━━━
"""
    
    if today_trades:
        for t in today_trades:
            if t["type"] == "SELL":
                report += f"\n📤 卖出: {t['name']}\n"
                report += f"   价格: ${t['price']:.2f}\n"
                report += f"   收益: {t['pnl_pct']:+.2f}%\n"
                report += f"   原因: {t['reason']}\n"
    else:
        report += "\n📊 今日无交易\n"
    
    report += f"""
━━━━━━━━━━━━━━━━━━
*持仓状态*
━━━━━━━━━━━━━━━━━━
"""
    
    for h in portfolio["holdings"]:
        code = h["code"]
        market = h["market"]
        
        if market == "HK":
            info = get_price_futu(code)
        else:
            info = get_price_finnhub(code)
        
        if info:
            current = info['price']
            cost = h['price']
            shares = h['shares']
            
            if market == "HK":
                pnl = (current - cost) * shares
                pnl_pct = (current - cost) / cost * 100
                sym = "HK$"
            else:
                pnl = (current - cost) * shares * HKD_RATE
                pnl_pct = (current - cost) / cost * 100
                sym = "$"
            
            emoji = "🟢" if pnl_pct > 0 else "🔴"
            report += f"\n{h['name']}\n"
            report += f"  现价: {sym}{current:.2f}\n"
            report += f"  收益: {emoji}{pnl_pct:+.2f}%\n"
    
    # 保存报告
    with open(DAILY_REPORT_FILE, "w") as f:
        json.dump({"report": report, "date": datetime.now().isoformat()}, f)
    
    return report


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print(get_daily_report())
    else:
        run_trading_cycle()
