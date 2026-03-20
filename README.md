# 量化交易系统 V3 | Quantitative Trading System V3

## 📁 目录结构

```
quant_trading/
├── setup/                     # 【第一部分】初始化
│   ├── api_config.py         # API配置（弹窗输入token/牛牛号密码）
│   ├── watchlist.py           # 选股列表（弹窗/文件编辑，支持分类）
│   └── __init__.py
│
├── data/                      # 数据层
│   ├── fetcher.py            # 数据获取（Futu/Finnhub/Yahoo）
│   └── storage.py            # 数据存储
│
├── strategies/                # 【第二部分】交易策略
│   ├── long_term/            # 长期策略
│   ├── swing/                # 波段策略
│   └── intraday/            # 日内策略
│
├── portfolio/                 # 持仓管理
│   └── manager.py
│
├── visualization/             # 【第三部分】可视化监控
│   └── dashboard.py          # 监控面板
│
├── config/
│   ├── config_v2.yaml        # 主配置
│   └── api_config.json       # API密钥（本地）
│
├── main.py                    # 主程序
└── requirements.txt           # 依赖
```

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行设置向导（首次）
python main.py --mode setup

# 3. 运行扫描
python main.py --mode all          # 全部扫描
python main.py --mode swing        # 仅波段
python main.py --mode intraday      # 仅日内
python main.py --mode dashboard      # 仅监控面板
```

## 📊 数据流程

```
1. setup/
   ↓ 用户输入 API token + 牛牛账号 + 选股列表
2. data/
   ↓ 获取市场数据（根据setup的配置）
3. strategies/
   → 三种策略计算（长线/波段/日内）
4. visualization/
   → 输出监控面板
```

## ⚙️ 设置说明

### API配置 (setup/api_config.py)

首次运行会提示输入：
- **Finnhub API Key**: https://finnhub.io/
- **富途 OpenD**: 牛牛号/密码
- **Alpha Vantage** (可选): https://www.alphavantage.co/

### 选股列表 (setup/watchlist.py)

支持分类：
- 港股自选
- 美股自选
- 按行业/板块分类

## 📈 策略说明

### 长期策略 (long_term)
- 持仓周期: 数月到数年
- 刷新频率: 每天1-2次
- 因子: 估值、成长、质量、动量

### 波段策略 (swing)
- 持仓周期: 2-5天
- 信号: RSI + MACD + 布林带
- 止损: -5%

### 日内策略 (intraday)
- 持仓周期: 当日
- 信号: 5分钟K线 + RSI超卖
- 止损: -3%

## 🛠️ 开发

### 添加新策略

```python
# strategies/my_strategy/strategy.py
from data.fetcher import DataFetcher

class MyStrategy:
    def __init__(self, config):
        self.fetcher = DataFetcher()
    
    def analyze(self, symbol, market):
        # 实现分析逻辑
        pass
```

## 📝 依赖

```
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
beautifulsoup4>=4.11.0
yfinance>=0.2.0
pyyaml>=6.0
lxml>=4.9.0
```

---
🦐 作者: 虾虾 | Author: 虾虾
