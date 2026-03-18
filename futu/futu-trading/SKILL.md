---
name: futu-trading
description: 富途 OpenAPI 交易接口 - 港股/美股/A股行情、模拟/真实交易（需 OpenD 运行在 127.0.0.1:11111）
requires:
  - python3
  - futu-api
---

# Futu Trading Skill

## 前提条件

1. **Mac/PC 上启动 Futu OpenD**
   - 下载: https://openapi.futusec.com/
   - 登录牛牛号
   - 保持运行

2. **安装 Python 库**
   ```bash
   pip install futu-api
   ```

## 可用命令

### 查询行情
```python
from futu import *

# 港股
q = OpenQuoteContext(host='127.0.0.1', port=11111)
ret, data = q.get_stock_quote(['HK.00700', 'HK.09988'])
print(data)
q.close()
```

### 模拟交易
```python
from futu import *

t = OpenTradeContext(host='127.0.0.1', port=11111)

# 模拟买入
ret, data = t.place_order(
    order_type=OrderType.NORMAL,
    side=TrdSide.BUY,
    code='HK.00700',
    price=500.0,
    qty=100,
    env=TrdEnv.SIMULATE
)
print(data)
t.close()
```

### 获取持仓
```python
from futu import *

t = OpenTradeContext(host='127.0.0.1', port=11111)
ret, data = t.get_position_list(env=TrdEnv.SIMULATE)
print(data)
t.close()
```

## 示例问题
- "查询港股 00700 行情"
- "用模拟账户买入 100 股腾讯"
- "查看当前持仓"
- "查询资金余额"
