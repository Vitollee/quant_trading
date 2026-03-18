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

## 🚀 富途 OpenAPI 配置指南

本系统支持通过**富途 OpenD** 获取实时港股行情和交易。

### 1. 下载 OpenD

从富途官网下载 Linux 命令行版：
https://openapi.futunn.com/futu-api-doc/quick/opend-base.html

选择 `Futu_OpenD_xxx_Ubuntu18.04` 版本

### 2. 启动 OpenD

```bash
cd Futu_OpenD_xxx_Ubuntu18.04
./FutuOpenD --login_account=你的牛牛号 --login_pwd=你的密码
```

**参数说明：**
- `--login_account` 牛牛号/手机号/邮箱
- `--login_pwd` 密码（明文）

**首次登录：**
- 需要在 APP 上完成问卷评估
- 登录成功后保持运行

### 3. 安装依赖

```bash
pip install futu-api pandas numpy
```

### 4. 测试行情

```python
from futu import OpenQuoteContext, SubType

q = OpenQuoteContext(host='127.0.0.1', port=11111)

# 订阅港股
q.subscribe(['HK.00700', 'HK.09988'], [SubType.QUOTE])

# 获取报价
ret, data = q.get_stock_quote(['HK.00700'])
print(data)

q.close()
```

### 5. 权限说明

| 市场 | 权限 |
|-----|------|
| 港股 | 默认 LV1 |
| 美股 | 需开通账户/购买 |

### 6. 常用端口

- 行情端口: 11111
- WebSocket: 8888（可选）

---
🦐
