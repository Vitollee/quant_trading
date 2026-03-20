#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化监控面板
功能: 生成交易信号和持仓的监控报告
作者: 虾虾 🦐
"""

from typing import List, Dict
from datetime import datetime
import json
import os


class Dashboard:
    """监控面板"""
    
    def __init__(self, output_dir: str = "portfolio"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, swing_signals: List[Dict], 
                      intraday_signals: List[Dict],
                      portfolio: Dict) -> str:
        """
        生成监控报告
        
        Returns:
            str: 报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/report_{timestamp}.json"
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "swing_signals": swing_signals,
            "intraday_signals": intraday_signals,
            "portfolio": portfolio,
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def print_summary(self, swing_signals: List[Dict],
                     intraday_signals: List[Dict],
                     portfolio: Dict):
        """打印摘要"""
        print("=" * 60)
        print("量化交易监控面板")
        print("=" * 60)
        print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 波段信号
        print(f"📊 波段交易信号 ({len(swing_signals)}个)")
        print("-" * 60)
        if swing_signals:
            print(f"{'代码':<8} {'市场':<4} {'价格':<10} {'得分':<6} {'信号'}")
            for s in swing_signals[:10]:
                print(f"{s['symbol']:<8} {s['market'].upper():<4} ${s['price']:<9.2f} {s['score']:<6.1f} {s.get('signal', 'N/A')}")
        else:
            print("  无信号")
        print()
        
        # 日内信号
        print(f"📈 日内交易信号 ({len(intraday_signals)}个)")
        print("-" * 60)
        if intraday_signals:
            print(f"{'代码':<8} {'价格':<10} {'入场':<10} {'止损':<10} {'目标'}")
            for s in intraday_signals[:10]:
                print(f"{s['symbol']:<8} ${s['price']:<9.2f} ${s.get('entry', 0):<9.2f} ${s.get('stop', 0):<9.2f} ${s.get('target', 0)}")
        else:
            print("  无信号")
        print()
        
        # 持仓状态
        print(f"💼 持仓状态")
        print("-" * 60)
        pos = portfolio.get("positions", [])
        if pos:
            for p in pos:
                print(f"  {p['symbol']} ({p['market']}): {p['quantity']}股 成本${p['avg_cost']:.2f}")
        else:
            print("  无持仓")
        print()
        
        print("=" * 60)
    
    def export_html(self, swing_signals: List[Dict],
                   intraday_signals: List[Dict],
                   portfolio: Dict) -> str:
        """导出HTML报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/report_{timestamp}.html"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>量化交易监控面板</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .buy {{ color: green; font-weight: bold; }}
        .sell {{ color: red; font-weight: bold; }}
        .watch {{ color: orange; }}
    </style>
</head>
<body>
    <h1>📊 量化交易监控面板</h1>
    <p>更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>📊 波段交易信号</h2>
    <table>
        <tr><th>代码</th><th>市场</th><th>价格</th><th>得分</th><th>信号</th><th>原因</th></tr>
        {''.join(f"<tr><td>{s['symbol']}</td><td>{s['market'].upper()}</td><td>${s['price']:.2f}</td><td>{s['score']:.1f}</td><td class='{s.get('signal', '').lower()}'>{s.get('signal', 'N/A')}</td><td>{s.get('reason', '')}</td></tr>" for s in swing_signals[:10])}
    </table>
    
    <h2>📈 日内交易信号</h2>
    <table>
        <tr><th>代码</th><th>价格</th><th>入场</th><th>止损</th><th>目标</th></tr>
        {''.join(f"<tr><td>{s['symbol']}</td><td>${s['price']:.2f}</td><td>${s.get('entry', 0):.2f}</td><td>${s.get('stop', 0):.2f}</td><td>${s.get('target', 0):.2f}</td></tr>" for s in intraday_signals[:10])}
    </table>
    
    <h2>💼 持仓</h2>
    <table>
        <tr><th>代码</th><th>市场</th><th>数量</th><th>成本</th></tr>
        {''.join(f"<tr><td>{p['symbol']}</td><td>{p['market']}</td><td>{p['quantity']}</td><td>${p['avg_cost']:.2f}</td></tr>" for p in portfolio.get('positions', []))}
    </table>
</body>
</html>
"""
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        
        return filename
