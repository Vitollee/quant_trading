# 量化交易系统 V2

基于 Vnstock 和 Screeni-py 设计思路改进

## 功能特点

### 📊 数据模块 (类似 Vnstock)
- 股票历史K线
- 实时报价
- 财务指标
- 简洁API设计

### 📈 技术指标 (类似 Screeni-py)
- RSI 相对强弱指标
- MACD 指数平滑异同移动平均线
- 布林带 Bollinger Bands
- ADX 趋势指标
- ATR 真实波动幅度
- SMA/EMA 均线

### 🔍 形态识别
- 早晨之星 (Morning Star)
- 黄昏之星 (Evening Star)
- 吞没形态 (Engulfing)
- 锤子线 (Hammer)
- 突破新高/新低

### 🎯 选股筛选
- 技术指标筛选
- 形态识别筛选
- 综合得分排序

## 快速开始

```python
from data.stock import StockData, TechnicalIndicators, PatternRecognition, StockScreener

# 1. 获取股票数据
stock = StockData("00700", "hk")
quote = stock.quote()

# 2. 计算技术指标
df = stock.history(period="3mo")
df = TechnicalIndicators.calculate(df)

# 3. 形态识别
patterns = PatternRecognition.recognize(df)
print(patterns)

# 4. 批量筛选
screener = StockScreener()
result = screener.screen(["00700", "09988"], "hk")
print(result)
```

## 运行脚本

```bash
cd /home/vito/Desktop/quant_trading
pip install yfinance pandas numpy

# 运行测试
python data/stock.py

# 运行主程序
python main.py --mode all
```

## 项目结构

```
quant_trading/
├── config/
│   ├── config.yaml        # V1 配置
│   └── config_v2.yaml    # V2 配置
├── data/
│   ├── fetcher.py        # 数据获取
│   └── stock.py          # V2 股票类 (改进版)
├── strategy/
│   ├── long_term/       # 长周期策略
│   └── intraday/         # 日内策略
├── trading/
│   └── engine.py         # 交易引擎
├── news/
│   └── fetcher.py        # 新闻
└── main.py               # 主程序
```

## 技术指标说明

| 指标 | 说明 | 用途 |
|-----|------|-----|
| RSI | 0-100 | <30超卖, >70超买 |
| MACD | 柱状图 | >0金叉, <0死叉 |
| 布林带 | 价格通道 | 触及上下轨反转 |
| ADX | 趋势强度 | >25强趋势 |

## 形态信号

| 形态 | 信号 |
|-----|-----|
| 早晨之星 | 🟢 买入 |
| 看涨吞没 | 🟢 买入 |
| 锤子线 | 🟢 买入 |
| 黄昏之星 | 🔴 卖出 |
| 看跌吞没 | 🔴 卖出 |

---
🦐 作者: 虾虾
