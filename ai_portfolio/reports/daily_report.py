#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日报告生成器
生成 AI 模拟组合的每日收益和交易报告
"""

import json
from datetime import datetime
import os

REPORT_DIR = "ai_portfolio/reports"
PORTFOLIO_DIR = "ai_portfolio"


def load_portfolios():
    """加载所有组合"""
    portfolios = {}
    
    # 长线
    with open(f"{PORTFOLIO_DIR}/longterm/portfolio.json", "r") as f:
        portfolios["longterm"] = json.load(f)
    
    # 波段
    with open(f"{PORTFOLIO_DIR}/swing/portfolio.json", "r") as f:
        portfolios["swing"] = json.load(f)
    
    # 日内
    with open(f"{PORTFOLIO_DIR}/daytrade/portfolio.json", "r") as f:
        portfolios["daytrade"] = json.load(f)
    
    return portfolios


def generate_report():
    """生成每日报告"""
    portfolios = load_portfolios()
    today = datetime.now().strftime("%Y-%m-%d")
    
    report = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "longterm": {
            "strategy": "长线投资",
            "total_cost_hkd": 0,
            "total_value_hkd": 0,
            "profit_hkd": 0,
            "profit_pct": 0,
            "trades": []
        },
        "swing": {
            "strategy": "波段交易",
            "total_cost_hkd": 0,
            "total_value_hkd": 0,
            "profit_hkd": 0,
            "profit_pct": 0,
            "trades": []
        },
        "daytrade": {
            "strategy": "日内交易",
            "total_cost_hkd": 0,
            "total_value_hkd": 0,
            "profit_hkd": 0,
            "profit_pct": 0,
            "trades": []
        },
        "summary": {
            "total_capital": 100000,
            "total_value_hkd": 0,
            "total_profit_hkd": 0,
            "total_profit_pct": 0
        }
    }
    
    return report


def save_report(report):
    """保存报告"""
    today = report["date"]
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    # 今日报告
    with open(f"{REPORT_DIR}/{today}.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 最新报告链接
    with open(f"{REPORT_DIR}/latest.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    report = generate_report()
    save_report(report)
    print(f"报告已生成: {REPORT_DIR}/{report['date']}.json")
    print(json.dumps(report, indent=2, ensure_ascii=False))
