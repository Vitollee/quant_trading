#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟投资组合跟踪
每天运行更新收益情况，支持港股+美股

用法: python portfolio_tracker.py
"""

import json
import requests
import yfinance as yf
from datetime import datetime

TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"
PORTFOLIO_FILE = "portfolio/simulated_portfolio.json"
HKD_RATE = 7.8  # USD to HKD


def get_current_price(code, market="US"):
    """获取当前价格（港股返回港币，美股返回美元）"""
    try:
        if market == "HK":
            # Yahoo Finance 港股
            s = yf.Ticker(code)
            hist = s.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]
                prev = s.history(period="2d")["Close"].iloc[0] if len(s.history(period="2d")) > 1 else price
                change = ((price - prev) / prev) * 100 if prev > 0 else 0
                return price, change, "HKD"
        else:
            # Finnhub 美股
            r = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol={code}&token={TOKEN}",
                timeout=5
            )
            data = r.json()
            if data.get("c", 0) > 0:
                return data.get("c", 0), data.get("dp", 0), "USD"
    except Exception as e:
        print(f"    错误: {e}")
    
    return 0, 0, "USD"


def update_portfolio():
    """更新组合收益"""
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
    
    # 分市场计算
    hk_value_hkd = 0  # 港股直接是港币
    hk_cost_hkd = 0
    us_value_usd = 0  # 美股是美元
    us_cost_usd = 0
    results = []
    
    print("=" * 80)
    print(f"📊 模拟投资组合 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"💰 总资金: {portfolio['capital_hkd']:,} HKD")
    print("=" * 80)
    
    for holding in portfolio["portfolio"]:
        code = holding["code"]
        shares = holding["shares"]
        buy_price = holding["buy_price"]
        market = holding.get("market", "US")
        
        current_price, change_pct, currency = get_current_price(code, market)
        
        if current_price > 0:
            current_value = current_price * shares
            profit = current_value - (buy_price * shares)
            profit_pct = (profit / (buy_price * shares)) * 100
            
            if market == "HK":
                hk_value_hkd += current_value
                hk_cost_hkd += buy_price * shares
            else:
                us_value_usd += current_value
                us_cost_usd += buy_price * shares
            
            results.append({
                "code": code,
                "name": holding["name"],
                "shares": shares,
                "buy_price": buy_price,
                "current_price": current_price,
                "cost": buy_price * shares,
                "value": current_value,
                "profit": profit,
                "profit_pct": profit_pct,
                "change_pct": change_pct,
                "market": market,
                "currency": currency,
                "reason": holding["reason"]
            })
    
    # 按收益排序
    results.sort(key=lambda x: x["profit_pct"], reverse=True)
    
    # 港股 (已经是港币)
    print(f"\n🇭🇰 港股持仓:")
    print(f"{'代码':<10} {'名称':<10} {'持股':<6} {'成本(HK$)':<12} {'现价(HK$)':<12} {'盈亏(HK$)':<12} {'收益率'}")
    print("-" * 80)
    for r in [x for x in results if x["market"] == "HK"]:
        emoji = "🟢" if r["profit_pct"] > 0 else "🔴"
        print(f"{r['code']:<10} {r['name']:<10} {r['shares']:<6} {r['buy_price']:<12.2f} {r['current_price']:<12.2f} {r['profit']:>+12.2f} {emoji}{r['profit_pct']:>+6.2f}%")
    
    # 美股 (美元)
    print(f"\n🇺🇸 美股持仓:")
    print(f"{'代码':<10} {'名称':<10} {'持股':<6} {'成本($)':<12} {'现价($)':<12} {'盈亏($)':<12} {'收益率'}")
    print("-" * 80)
    for r in [x for x in results if x["market"] == "US"]:
        emoji = "🟢" if r["profit_pct"] > 0 else "🔴"
        print(f"{r['code']:<10} {r['name']:<10} {r['shares']:<6} {r['buy_price']:<12.2f} {r['current_price']:<12.2f} {r['profit']:>+12.2f} {emoji}{r['profit_pct']:>+6.2f}%")
    
    print("-" * 80)
    
    # 总收益计算
    # 港股换算成美元
    hk_value_usd = hk_value_hkd / HKD_RATE
    hk_cost_usd = hk_cost_hkd / HKD_RATE
    total_value_usd = hk_value_usd + us_value_usd
    total_cost_usd = hk_cost_usd + us_cost_usd
    
    total_profit_usd = total_value_usd - total_cost_usd
    total_profit_pct = (total_profit_usd / total_cost_usd) * 100
    
    # 换算HKD
    total_value_hkd = total_value_usd * HKD_RATE
    total_cost_hkd = total_cost_usd * HKD_RATE
    total_profit_hkd = total_profit_usd * HKD_RATE
    cash_hkd = portfolio.get("cash_hkd", 0)
    
    print(f"\n💵 总资产: ${total_value_usd:.2f} ({total_value_hkd:,.0f} HKD)")
    print(f"💸 成本: ${total_cost_usd:.2f} ({total_cost_hkd:,.0f} HKD)")
    print(f"📈 总收益: ${total_profit_usd:.2f} ({total_profit_hkd:>+,.0f} HKD)")
    print(f"📊 收益率: {total_profit_pct:+.2f}%")
    
    # 市场分布
    hk_pct = (hk_value_usd / total_value_usd * 100) if total_value_usd > 0 else 0
    us_pct = (us_value_usd / total_value_usd * 100) if total_value_usd > 0 else 0
    print(f"\n📊 市场分布:")
    print(f"  🇭🇰 港股: HK${hk_value_hkd:,.0f} ({hk_pct:.1f}%)")
    print(f"  🇺🇸 美股: ${us_value_usd:,.2f} ({us_pct:.1f}%)")
    print(f"  💰 现金: {cash_hkd:,} HKD")
    
    # 总资产含现金
    total_with_cash = total_value_hkd + cash_hkd
    print(f"\n💎 总资产(含现金): {total_with_cash:,.0f} HKD")
    
    # 每日涨跌
    today_change = sum(r["change_pct"] for r in results) / len(results) if results else 0
    print(f"📅 今日组合平均涨跌: {today_change:+.2f}%")
    
    # Top picks 分析
    print("\n" + "=" * 80)
    print("🏆 持仓分析 (按收益排序):")
    print("-" * 80)
    
    for i, r in enumerate(results[:3], 1):
        sym = "HK$" if r["market"] == "HK" else "$"
        print(f"\n{i}. {r['code']} {r['name']}")
        print(f"   现价: {sym}{r['current_price']:.2f} ({r['change_pct']:+.2f}%)")
        print(f"   收益率: {r['profit_pct']:+.2f}% ({r['profit']:>+10.2f})")
        print(f"   理由: {r['reason']}")
    
    print("\n" + "=" * 80)
    
    # 保存结果
    result_data = {
        "date": datetime.now().isoformat(),
        "total_value_usd": total_value_usd,
        "total_cost_usd": total_cost_usd,
        "profit_usd": total_profit_usd,
        "profit_pct": total_profit_pct,
        "total_value_hkd": total_with_cash,
        "cash_hkd": cash_hkd,
        "hk_value_hkd": hk_value_hkd,
        "us_value_usd": us_value_usd,
        "today_change_pct": today_change,
        "holdings": results
    }
    
    with open("portfolio/daily_result.json", "w") as f:
        json.dump(result_data, f, indent=2)
    
    return result_data


if __name__ == "__main__":
    update_portfolio()
