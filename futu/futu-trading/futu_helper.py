#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途交易助手
快速查询和交易

用法:
    python futu_helper.py quote 00700        # 查询行情
    python futu_helper.py buy 00700 500 100 # 买入
    python futu_helper.py positions          # 查持仓
    python futu_helper.py balance            # 查资金
"""

import sys
from futu import *

HOST = '127.0.0.1'
PORT = 11111


def get_quote(symbols):
    """查询行情"""
    quote_ctx = OpenQuoteContext(host=HOST, port=PORT)
    ret, data = quote_ctx.get_stock_quote(symbols)
    if ret == 0:
        print(data)
    else:
        print(f"Error: {data}")
    quote_ctx.close()


def buy(code, price, qty):
    """买入"""
    trd_ctx = OpenTradeContext(host=HOST, port=PORT)
    ret, data = trd_ctx.place_order(
        order_type=OrderType.NORMAL,
        side=TrdSide.BUY,
        code=f"HK.{code}",
        price=float(price),
        qty=int(qty),
        env=TrdEnv.SIMULATE
    )
    if ret == 0:
        print(data)
    else:
        print(f"Error: {data}")
    trd_ctx.close()


def sell(code, price, qty):
    """卖出"""
    trd_ctx = OpenTradeContext(host=HOST, port=PORT)
    ret, data = trd_ctx.place_order(
        order_type=OrderType.NORMAL,
        side=TrdSide.SELL,
        code=f"HK.{code}",
        price=float(price),
        qty=int(qty),
        env=TrdEnv.SIMULATE
    )
    if ret == 0:
        print(data)
    else:
        print(f"Error: {data}")
    trd_ctx.close()


def positions():
    """查持仓"""
    trd_ctx = OpenTradeContext(host=HOST, port=PORT)
    ret, data = trd_ctx.get_position_list(env=TrdEnv.SIMULATE)
    if ret == 0:
        print(data)
    else:
        print(f"Error: {data}")
    trd_ctx.close()


def balance():
    """查资金"""
    trd_ctx = OpenTradeContext(host=HOST, port=PORT)
    ret, data = trd_ctx.get_account_list(env=TrdEnv.SIMULATE)
    if ret == 0:
        print(data)
    else:
        print(f"Error: {data}")
    trd_ctx.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "quote":
        symbols = sys.argv[2:] if len(sys.argv) > 2 else ["HK.00700"]
        get_quote(symbols)
    elif cmd == "buy":
        if len(sys.argv) < 5:
            print("用法: python futu_helper.py buy <代码> <价格> <数量>")
            sys.exit(1)
        buy(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "sell":
        if len(sys.argv) < 5:
            print("用法: python futu_helper.py sell <代码> <价格> <数量>")
            sys.exit(1)
        sell(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "positions":
        positions()
    elif cmd == "balance":
        balance()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
