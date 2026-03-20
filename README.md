# 量化交易系统 V2 | Quantitative Trading System V2

基于 Vnstock 和 Screeni-py 设计思路改进 | Built on Vnstock and Screeni-py concepts

## 功能特点 | Features

### 📊 数据模块 | Data Module
- 股票历史K线 | Stock Historical K-lines
- 实时报价 | Real-time Quotes
- 财务指标 | Financial Indicators
- 简洁API设计 | Clean API Design

### 📈 技术指标 | Technical Indicators
- RSI 相对强弱指标 | Relative Strength Index
- MACD 指数平滑异同移动平均线 | Moving Average Convergence Divergence
- 布林带 Bollinger Bands
- ADX 趋势指标 | Average Directional Index
- ATR 真实波动幅度 | Average True Range
- SMA/EMA 均线 | Simple/Exponential Moving Averages

### 🔍 形态识别 | Pattern Recognition
- 早晨之星 | Morning Star
- 黄昏之星 | Evening Star
- 吞没形态 | Engulfing Pattern
- 锤子线 | Hammer
- 突破新高/新低 | Breakout High/Low

### 🎯 选股筛选 | Stock Screening
- 技术指标筛选 | Technical Indicator Filters
- 形态识别筛选 | Pattern Recognition Filters
- 综合得分排序 | Comprehensive Scoring

## 快速开始 | Quick Start

```python
from data.stock import StockData, TechnicalIndicators, PatternRecognition, StockScreener

# 1. 获取股票数据 | Get Stock Data
stock = StockData("00700", "hk")
quote = stock.quote()

# 2. 计算技术指标 | Calculate Technical Indicators
df = stock.history(period="3mo")
df = TechnicalIndicators.calculate(df)

# 3. 形态识别 | Pattern Recognition
patterns = PatternRecognition.recognize(df)
print(patterns)

# 4. 批量筛选 | Batch Screening
screener = StockScreener()
result = screener.screen(["00700", "09988"], "hk")
print(result)
```

## 运行脚本 | Run Scripts

```bash
cd ~/Desktop/quant_trading

# 安装依赖 | Install Dependencies
pip install -r requirements.txt

# 运行测试 | Run Test
python data/stock.py

# 运行主程序 | Run Main
python main.py --mode all
```

**依赖包 | Dependencies:**
```
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
beautifulsoup4>=4.11.0
yfinance>=0.2.0
pyyaml>=6.0
lxml>=4.9.0
```

## 项目结构 | Project Structure

```
quant_trading/
├── config/
│   ├── config.yaml        # V1 配置 | V1 Config
│   └── config_v2.yaml    # V2 配置 | V2 Config
├── data/
│   ├── fetcher.py        # 数据获取 | Data Fetcher
│   ├── stock.py          # V2 股票类 | V2 Stock Class
│   ├── sector.py         # 板块分析 | Sector Analysis
│   └── scoring.py         # 评分系统 | Scoring System
├── strategy/
│   ├── long_term/        # 长周期策略 | Long-term Strategy
│   └── intraday/         # 日内策略 | Intraday Strategy
├── trading/
│   └── engine.py          # 交易引擎 | Trading Engine
├── portfolio/
│   ├── ai_portfolio.json    # AI组合 | AI Portfolio
│   ├── ai_tracker.py        # 组合追踪 | Portfolio Tracker
│   └── hk_trading_signals.json  # 港股信号 | HK Signals
├── news/
│   └── fetcher.py         # 新闻 | News
├── scripts/
│   ├── futu_healthcheck.py  # Futu健康检查 | Futu Health Check
│   └── restart_futu.sh      # Futu重启脚本 | Futu Restart Script
└── main.py                 # 主程序 | Main Program
```

## 技术指标说明 | Technical Indicators Guide

| 指标 | Indicator | 说明 | Description | 用途 | Usage |
|-----|-----------|-----|-------------|-----|-------|
| RSI | RSI | 0-100 | 0-100 | <30超卖, >70超买 | <30 oversold, >70 overbought |
| MACD | MACD | 柱状图 | Histogram | >0金叉, <0死叉 | >0 golden cross, <0 death cross |
| 布林带 | Bollinger | 价格通道 | Price channel | 触及上下轨反转 | Reversal at upper/lower band |
| ADX | ADX | 趋势强度 | Trend strength | >25强趋势 | >25 strong trend |

## 形态信号 | Pattern Signals

| 形态 | Pattern | 信号 | Signal |
|-----|---------|-----|--------|
| 早晨之星 | Morning Star | 🟢 买入 | 🟢 Buy |
| 看涨吞没 | Bullish Engulfing | 🟢 买入 | 🟢 Buy |
| 锤子线 | Hammer | 🟢 买入 | 🟢 Buy |
| 黄昏之星 | Evening Star | 🔴 卖出 | 🔴 Sell |
| 看跌吞没 | Bearish Engulfing | 🔴 卖出 | 🔴 Sell |

## 投资组合 | Portfolio

### AI智能组合 | AI Smart Portfolio
- 长线投资: MU, NVDA, GOOGL, MSFT
- 港股: 小米, 腾讯, 舜宇光学, 中国神华
- 每日自动追踪 | Daily Auto-tracking

### 交易信号 | Trading Signals
- Swing Trade (波段交易): 2-5天持仓
- Day Trade (日内交易): 当日平仓
- 严格止损 -3% | Stop Loss -3%

---
🦐 作者: 虾虾 | Author: 虾虾

---

## 🚀 富途 OpenAPI 配置 | Futu OpenAPI Setup

本系统支持通过**富途 OpenD** 获取实时港股行情和交易。
This system supports real-time HK stock data via **Futu OpenD**.

### 1. 下载 OpenD | Download OpenD

从富途官网下载 Linux 命令行版：
Download from Futu official website:
https://openapi.futunn.com/futu-api-doc/quick/opend-base.html

选择 `Futu_OpenD_xxx_Ubuntu18.04` 版本 | Select `Futu_OpenD_xxx_Ubuntu18.04`

### 2. 启动 OpenD | Start OpenD

```bash
cd Futu_OpenD_xxx_Ubuntu18.04
./FutuOpenD --login_account=你的牛牛号/phone --login_pwd=密码
```

**参数说明 | Parameters:**
- `--login_account` 牛牛号/手机号/邮箱 | Phone/Email
- `--login_pwd` 密码（明文）| Password (plain text)

**首次登录 | First Login:**
- 需要在 APP 上完成问卷评估 | Complete questionnaire in APP
- 登录成功后保持运行 | Keep running after successful login

### 3. 安装依赖 | Install Dependencies

```bash
pip install futu-api pandas numpy
```

### 4. 测试行情 | Test Quote

```python
from futu import OpenQuoteContext, SubType

q = OpenQuoteContext(host='127.0.0.1', port=11111)

# 订阅港股 | Subscribe HK stocks
q.subscribe(['HK.00700', 'HK.09988'], [SubType.QUOTE])

# 获取报价 | Get Quote
ret, data = q.get_stock_quote(['HK.00700'])
print(data)

q.close()
```

### 5. 权限说明 | Permissions

| 市场 | Market | 权限 | Permission |
|-----|--------|-----|------------|
| 港股 | HK Stocks | 默认 LV1 | Default LV1 |
| 美股 | US Stocks | 需开通账户/购买 | Account required/Purchase |

### 6. 常用端口 | Common Ports

- 行情端口 | Quote Port: 11111
- WebSocket: 8888 (可选 | Optional)

---

## 📊 API 数据源 | Data Sources

| 数据源 | Source | 用途 | Usage |
|-------|--------|-----|-------|
| Futu OpenD | Futu OpenD | 港股实时行情 | HK Real-time Quotes |
| Finnhub | Finnhub | 美股数据 | US Stock Data |
| Yahoo Finance | Yahoo Finance | 历史数据备份 | Historical Data Backup |

---

🦐 虾虾量化交易系统 | 虾虾 Quantitative Trading System
