#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途 OpenAPI 集成模块
连接本地 OpenD 网关获取行情和交易

使用:
1. Mac 启动富途量化管理器 (OpenD)
2. 运行此脚本

作者: 虾虾 🦐
"""

from futu import *
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FutuAPI:
    """富途 API 封装"""
    
    # 市场常量
    MARKET_HK = 1   # 港股
    MARKET_US = 2   # 美股
    MARKET_CN = 6   # A股
    MARKET_SG = 3   # 新加坡
    MARKET_JP = 5   # 日本
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        
    def connect(self) -> bool:
        """连接 OpenD"""
        try:
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            logger.info(f"连接 OpenD 成功: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def login(self, encrypted_pwd: str = "", pwd: str = "", env: int = 1) -> bool:
        """
        登录交易账号
        
        Args:
            encrypted_pwd: 加密密码
            pwd: 原始密码
            env: 1=模拟交易 0=实盘
        """
        try:
            # 行情不需要登录，直接用
            # 交易需要先登录
            logger.info(f"交易环境: {'模拟' if env == 1 else '实盘'}")
            return True
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    # ==================== 行情接口 ====================
    
    def get_quote(self, symbol: str, market: str = "HK") -> Optional[Dict]:
        """
        获取实时报价
        
        Args:
            symbol: 股票代码 (如 00700, AAPL)
            market: 市场 (HK, US, CN, SG, JP)
            
        Returns:
            dict: 报价数据
        """
        if not self.quote_ctx:
            return None
            
        market_id = self._get_market_id(market)
        
        try:
            ret, data = self.quote_ctx.get_stock_quote([symbol])
            if ret == 0 and not data.empty:
                row = data.iloc[0]
                return {
                    "symbol": symbol,
                    "name": row.get('name', ''),
                    "last_price": row.get('last_price', 0),
                    "open": row.get('open_price', 0),
                    "high": row.get('high_price', 0),
                    "low": row.get('low_price', 0),
                    "volume": row.get('volume', 0),
                    "turnover": row.get('turnover', 0),
                    "change": row.get('change_val', 0),
                    "change_pct": row.get('change_rate', 0),
                    "bid": row.get('bid_price', 0),
                    "ask": row.get('ask_price', 0),
                }
            return None
        except Exception as e:
            logger.error(f"获取报价失败: {e}")
            return None
    
    def get_history(self, symbol: str, start: str, end: str, 
                   market: str = "HK", ktype: str = "DAY") -> List[Dict]:
        """
        获取历史K线
        
        Args:
            symbol: 股票代码
            start: 开始日期 (YYYY-MM-DD)
            end: 结束日期 (YYYY-MM-DD)
            market: 市场
            ktype: K线类型 (DAY, WEEK, MONTH, 1M, 5M, 15M, 30M, 60M, 1H, 2H, 4H)
            
        Returns:
            list: K线数据
        """
        if not self.quote_ctx:
            return []
            
        try:
            # 转换K线类型
            kt_map = {
                "DAY": KL_TYPE.KL_DAY,
                "WEEK": KL_TYPE.KL_WEEK,
                "MONTH": KL_TYPE.KL_MONTH,
                "1M": KL_TYPE.KL_1M,
                "5M": KL_TYPE.KL_5M,
                "15M": KL_TYPE.KL_15M,
                "30M": KL_TYPE.KL_30M,
                "60M": KL_TYPE.KL_60M,
                "1H": KL_TYPE.KL_1H,
                "2H": KL_TYPE.KL_2H,
                "4H": KL_TYPE.KL_4H,
            }
            kl_type = kt_map.get(ktype, KL_TYPE.KL_DAY)
            
            ret, data = self.quote_ctx.get_history_kline(
                symbol, start, end, kl_type, ""
            )
            if ret == 0 and not data.empty:
                return data.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
            return []
    
    def get_realtime_kline(self, symbol: str, market: str = "HK",
                          ktype: str = "DAY", count: int = 100) -> List[Dict]:
        """获取实时K线"""
        if not self.quote_ctx:
            return []
            
        try:
            kt_map = {
                "DAY": KL_TYPE.KL_DAY,
                "5M": KL_TYPE.KL_5M,
                "15M": KL_TYPE.KL_15M,
                "30M": KL_TYPE.KL_30M,
                "60M": KL_TYPE.KL_60M,
            }
            kl_type = kt_map.get(ktype, KL_TYPE.KL_DAY)
            
            ret, data = self.quote_ctx.get_realtime_kline(
                symbol, count, kl_type
            )
            if ret == 0 and not data.empty:
                return data.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"获取实时K线失败: {e}")
            return []
    
    # ==================== 交易接口 ====================
    
    def open_trade(self, encrypted_pwd: str = "", pwd: str = "", 
                  env: int = 1) -> bool:
        """打开交易接口"""
        try:
            self.trade_ctx = OpenTradeContext(
                host=self.host,
                port=self.port,
                is_encrypt=True
            )
            # 登录
            if pwd:
                ret = self.trade_ctx.login(pwd=pwd, encrypted=False, env=env)
                if ret == 0:
                    logger.info("交易登录成功")
                    return True
            return False
        except Exception as e:
            logger.error(f"打开交易接口失败: {e}")
            return False
    
    def buy(self, symbol: str, price: float, qty: int, 
           market: str = "HK", order_type: str = "NORMAL", env: int = 1) -> Dict:
        """
        买入
        
        Args:
            symbol: 股票代码
            price: 价格
            qty: 数量
            market: 市场
            order_type: NORMAL=普通, MARKET=市价
            env: 1=模拟 0=实盘
        """
        if not self.trade_ctx:
            return {"ret": -1, "msg": "未打开交易接口"}
            
        try:
            ret, data = self.trade_ctx.place_order(
                order_type=OrderType.NORMAL if order_type == "NORMAL" else OrderType.MARKET,
                side=TrdSide.BUY,
                code=symbol,
                price=price,
                qty=qty,
                env=env
            )
            if ret == 0:
                return {"ret": 0, "data": data.to_dict() if hasattr(data, 'to_dict') else str(data)}
            return {"ret": ret, "msg": str(data)}
        except Exception as e:
            return {"ret": -1, "msg": str(e)}
    
    def sell(self, symbol: str, price: float, qty: int,
            market: str = "HK", order_type: str = "NORMAL", env: int = 1) -> Dict:
        """卖出"""
        if not self.trade_ctx:
            return {"ret": -1, "msg": "未打开交易接口"}
            
        try:
            ret, data = self.trade_ctx.place_order(
                order_type=OrderType.NORMAL if order_type == "NORMAL" else OrderType.MARKET,
                side=TrdSide.SELL,
                code=symbol,
                price=price,
                qty=qty,
                env=env
            )
            if ret == 0:
                return {"ret": 0, "data": data.to_dict() if hasattr(data, 'to_dict') else str(data)}
            return {"ret": ret, "msg": str(data)}
        except Exception as e:
            return {"ret": -1, "msg": str(e)}
    
    def get_positions(self, env: int = 1) -> List[Dict]:
        """获取持仓"""
        if not self.trade_ctx:
            return []
            
        try:
            ret, data = self.trade_ctx.get_position_list(env=env)
            if ret == 0 and not data.empty:
                return data.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    def get_balance(self, env: int = 1) -> Dict:
        """获取账户资金"""
        if not self.trade_ctx:
            return {}
            
        try:
            ret, data = self.trade_ctx.get_account_list(env=env)
            if ret == 0 and not data.empty:
                return data.iloc[0].to_dict()
            return {}
        except Exception as e:
            logger.error(f"获取资金失败: {e}")
            return {}
    
    def get_orders(self, env: int = 1) -> List[Dict]:
        """获取订单列表"""
        if not self.trade_ctx:
            return []
            
        try:
            ret, data = self.trade_ctx.get_order_list(env=env)
            if ret == 0 and not data.empty:
                return data.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return []
    
    # ==================== 工具 ====================
    
    def _get_market_id(self, market: str) -> int:
        """市场字符串转ID"""
        m = market.upper()
        if m == "HK":
            return self.MARKET_HK
        elif m == "US":
            return self.MARKET_US
        elif m == "CN":
            return self.MARKET_CN
        elif m == "SG":
            return self.MARKET_SG
        elif m == "JP":
            return self.MARKET_JP
        return self.MARKET_HK
    
    def close(self):
        """关闭连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        logger.info("连接已关闭")


# ==================== 使用示例 ====================
if __name__ == "__main__":
    print("=== 富途 API 测试 ===")
    
    # 创建客户端
    api = FutuAPI()
    
    # 连接 OpenD
    if api.connect():
        # 获取港股报价
        quote = api.get_quote("00700", "HK")
        print(f"腾讯: {quote}")
        
        # 获取美股报价
        quote = api.get_quote("AAPL", "US")
        print(f"Apple: {quote}")
        
        # 获取历史K线
        klines = api.get_history("00700", "2026-01-01", "2026-03-18", "HK", "DAY")
        print(f"K线数量: {len(klines)}")
        
        # 打开交易
        # api.open_trade(pwd="你的交易密码", env=1)  # 模拟
        
        api.close()
    else:
        print("请先启动富途量化管理器 (OpenD)")
