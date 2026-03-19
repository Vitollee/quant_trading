#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能投资组合每日追踪
推送每日收益报告到 WhatsApp
"""

import json
import requests
import yfinance as yf
from futu import OpenQuoteContext, SubType
from datetime import datetime

TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"
PORTFOLIO_FILE = "portfolio/ai_portfolio.json"
HKD_RATE = 7.8


def get_price(code, market="US"):
    """获取价格"""
    try:
        if market == "HK":
            s = yf.Ticker(code)
            h = s.history(period="1d")
            if not h.empty:
                return h["Close"].iloc[-1], 0
        else:
            r = requests.get(f"https://finnhub.io/api/v1/quote?symbol={code}&token={TOKEN}", timeout=5)
            d = r.json()
            if d.get("c", 0) > 0:
                return d.get("c", 0), d.get("dp", 0)
    except:
        pass
    return 0, 0


def get_futu_price(code):
    """从 Futu 获取港股价格"""
    try:
        ctx = OpenQuoteContext('127.0.0.1', 11111)
        ctx.subscribe([code], [SubType.QUOTE], True)
        import time
        time.sleep(0.5)
        ret, data = ctx.get_stock_quote([code])
        ctx.close()
        if ret == 0 and not data.empty:
            return data.iloc[0]['last_price'], 0
    except:
        pass
    return 0, 0


def update():
    """更新组合收益"""
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
    
    total_value_hkd = 0
    total_cost_hkd = 0
    results = []
    
    for h in portfolio["holdings"]:
        code = h["code"]
        market = h["market"]
        shares = h["shares"]
        buy_price = h["price"]
        
        # 获取当前价格
        if market == "HK":
            current_price, change = get_futu_price(code)
        else:
            current_price, change = get_price(code, market)
        
        if current_price > 0:
            if market == "HK":
                current_value_hkd = current_price * shares
                cost_hkd = buy_price * shares
            else:
                current_value_hkd = current_price * shares * HKD_RATE
                cost_hkd = buy_price * shares * HKD_RATE
            
            profit_hkd = current_value_hkd - cost_hkd
            profit_pct = (profit_hkd / cost_hkd) * 100
            
            results.append({
                "code": code,
                "name": h["name"],
                "shares": shares,
                "buy_price": buy_price,
                "current_price": current_price,
                "current_value_hkd": current_value_hkd,
                "cost_hkd": cost_hkd,
                "profit_hkd": profit_hkd,
                "profit_pct": profit_pct,
                "change": change,
                "market": market,
                "reason": h["reason"]
            })
            
            total_value_hkd += current_value_hkd
            total_cost_hkd += cost_hkd
    
    # 按收益排序
    results.sort(key=lambda x: x["profit_pct"], reverse=True)
    
    # 总收益
    total_profit_hkd = total_value_hkd - total_cost_hkd
    total_profit_pct = (total_profit_hkd / total_cost_hkd) * 100
    
    # 格式化报告
    report = f"""
📊 *AI智能投资组合*
{datetime.now().strftime('%Y-%m-%d %H:%M')}

━━━━━━━━━━━━━━━━━━
*收益概览*
━━━━━━━━━━━━━━━━━━
💰 总资产: HK${total_value_hkd:,.0f}
💸 成本: HK${total_cost_hkd:,.0f}
📈 总收益: *HK${total_profit_hkd:+,.0f}*
📊 收益率: *{total_profit_pct:+.2f}%*

━━━━━━━━━━━━━━━━━━
*持仓明细*
━━━━━━━━━━━━━━━━━━
"""
    
    for r in results:
        emoji = "🟢" if r["profit_pct"] > 0 else "🔴"
        sym = "HK$" if r["market"] == "HK" else "$"
        report += f"\n{r['name']}\n"
        report += f"  {sym}{r['current_price']:.2f} ({r['change']:+.2f}%)\n"
        report += f"  {emoji}收益: {r['profit_pct']:+.2f}%\n"
    
    # Top pick
    if results:
        top = results[0]
        report += f"""
━━━━━━━━━━━━━━━━━━
*🏆 最佳表现*
━━━━━━━━━━━━━━━━━━
{top['name']}: {top['profit_pct']:+.2f}%
原因: {top['reason']}
"""
    
    # 风险提示
    if total_profit_pct < -3:
        report += """
⚠️ *建议关注*
组合亏损超过3%，考虑是否止损
"""
    
    # 保存结果
    with open("portfolio/daily_ai_result.json", "w") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "total_value_hkd": total_value_hkd,
            "total_cost_hkd": total_cost_hkd,
            "profit_hkd": total_profit_hkd,
            "profit_pct": total_profit_pct,
            "holdings": results
        }, f, indent=2, ensure_ascii=False)
    
    return report


if __name__ == "__main__":
    print(update())
