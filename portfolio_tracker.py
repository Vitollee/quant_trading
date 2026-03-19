#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟投资组合跟踪
每天运行更新收益情况

用法: python portfolio_tracker.py
"""

import json
import requests
import yfinance as yf
from datetime import datetime

TOKEN = "d6tf93hr01qhkb43v280d6tf93hr01qhkb43v28g"
PORTFOLIO_FILE = "portfolio/simulated_portfolio.json"


def get_current_price(code):
    """获取当前价格"""
    try:
        r = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={code}&token={TOKEN}",
            timeout=5
        )
        data = r.json()
        return data.get("c", 0), data.get("dp", 0)
    except:
        # 备用 Yahoo Finance
        try:
            s = yf.Ticker(code)
            hist = s.history(period="1d")
            if not hist.empty:
                return hist["Close"].iloc[-1], 0
        except:
            pass
        return 0, 0


def update_portfolio():
    """更新组合收益"""
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
    
    total_value = 0
    total_cost = 0
    results = []
    
    print("=" * 70)
    print(f"📊 模拟投资组合 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"💰 总资金: {portfolio['capital_hkd']:,} HKD")
    print("=" * 70)
    
    for holding in portfolio["portfolio"]:
        code = holding["code"]
        shares = holding["shares"]
        buy_price = holding["buy_price"]
        cost = buy_price * shares
        
        current_price, change_pct = get_current_price(code)
        
        if current_price > 0:
            current_value = current_price * shares
            profit = current_value - cost
            profit_pct = (profit / cost) * 100
            
            total_value += current_value
            total_cost += cost
            
            results.append({
                "code": code,
                "name": holding["name"],
                "shares": shares,
                "buy_price": buy_price,
                "current_price": current_price,
                "cost": cost,
                "value": current_value,
                "profit": profit,
                "profit_pct": profit_pct,
                "change_pct": change_pct,
                "reason": holding["reason"]
            })
    
    # 按收益排序
    results.sort(key=lambda x: x["profit_pct"], reverse=True)
    
    print(f"\n{'代码':<8} {'名称':<12} {'持股':<4} {'成本':<8} {'现价':<8} {'价值':<10} {'盈亏':<10} {'收益率'}")
    print("-" * 90)
    
    for r in results:
        emoji = "🟢" if r["profit_pct"] > 0 else "🔴"
        print(f"{r['code']:<8} {r['name']:<12} {r['shares']:<4} ${r['buy_price']:<7.2f} ${r['current_price']:<7.2f} ${r['value']:<9.2f} {r['profit']:>+8.2f} {emoji}{r['profit_pct']:>+6.2f}%")
    
    print("-" * 90)
    
    # 总收益
    total_profit = total_value - total_cost
    total_profit_pct = (total_profit / total_cost) * 100
    
    # 换算HKD
    total_value_hkd = total_value * 7.8
    total_cost_hkd = total_cost * 7.8
    total_profit_hkd = total_profit * 7.8
    
    print(f"\n💵 总资产: ${total_value:.2f} ({total_value_hkd:,.0f} HKD)")
    print(f"💸 成本: ${total_cost:.2f} ({total_cost_hkd:,.0f} HKD)")
    print(f"📈 总收益: ${total_profit:.2f} ({total_profit_hkd:>+,.0f} HKD)")
    print(f"📊 收益率: {total_profit_pct:+.2f}%")
    
    # 现金
    cash_usd = portfolio.get("cash_hkd", 0) / 7.8
    print(f"💰 现金: ${cash_usd:.2f} ({portfolio.get('cash_hkd', 0):,} HKD)")
    
    total_with_cash_hkd = total_value_hkd + portfolio.get("cash_hkd", 0)
    print(f"\n💎 总资产(含现金): {total_with_cash_hkd:,.0f} HKD")
    
    # 每日涨跌
    today_change = sum(r["change_pct"] for r in results) / len(results) if results else 0
    print(f"📅 今日板块平均涨跌: {today_change:+.2f}%")
    
    # Top picks 分析
    print("\n" + "=" * 70)
    print("🏆 持仓分析:")
    print("-" * 70)
    
    for r in results[:3]:
        print(f"\n{r['code']} {r['name']}")
        print(f"  现价: ${r['current_price']:.2f} ({r['change_pct']:+.2f}%)")
        print(f"  收益率: {r['profit_pct']:+.2f}%")
        print(f"  理由: {r['reason'][:50]}...")
    
    print("\n" + "=" * 70)
    
    # 保存结果
    with open("portfolio/daily_result.json", "w") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "total_value_usd": total_value,
            "total_cost_usd": total_cost,
            "profit_usd": total_profit,
            "profit_pct": total_profit_pct,
            "total_value_hkd": total_with_cash_hkd,
            "holdings": results
        }, f, indent=2)
    
    return results


if __name__ == "__main__":
    update_portfolio()
