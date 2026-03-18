#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途 OpenAPI 简单集成
使用官方 futu-api 库

安装: pip install futu-api

作者: 虾虾 🦐
"""

try:
    from futu import *
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    print("Warning: futu-api not installed. Run: pip install futu-api")

from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FutuTrader:
    """富途交易客户端"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        """
        初始化
        
        Args:
            host: 富途量化管理器地址
            port: 端口
        """
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        
    def connect(self, conn_key: str, crypto: object = None) -> bool:
        """连接"""
        if not FUTU_AVAILABLE:
            logger.error("futu-api not installed")
            return False
            
        try:
            # 行情连接
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            logger.info("行情连接成功")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def login(self, conn_key: str, pwd: str = "", env: int = 1) -> bool:
        """
        登录交易账号
        
        Args:
            conn_key: 连接密钥
            pwd: 交易密码 (可选)
            env: 1=模拟 0=实盘
        """
        if not self.quote_ctx:
            return False
            
        try:
            # 交易账号登录
            self.trade_ctx = OpenTradeContext(
                host=self.host, 
                port=self.port,
                is_encrypt=True
            )
            logger.info("交易登录成功")
            return True
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    def get_quote(self, symbol: str, market: str = "HK") -> Optional[Dict]:
        """
        获取实时报价
        
        Args:
            symbol: 股票代码 (如 00700)
            market: 市场 HK/US/CN
            
        Returns:
            dict: 报价
        """
        if not self.quote_ctx:
            return None
            
        try:
            ret, data = self.quote_ctx.get_stock_quote([symbol])
            if ret == 0:
                return data.iloc[0].to_dict()
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
            start: 开始日期
            end: 结束日期
            market: 市场
            ktype: K线类型 DAY/WEEK/MONTH
        """
        if not self.quote_ctx:
            return []
            
        try:
            ret, data = self.quote_ctx.get_history_kline(
                symbol, start, end, ktype, ""
            )
            if ret == 0:
                return data.to_dict('records')
            return []
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
            return []
    
    def place_order(self, symbol: str, side: str, price: float, 
                   qty: int, order_type: str = "NORMAL", 
                   env: int = 1) -> Dict:
        """
        下单
        
        Args:
            symbol: 股票代码
            side: 买入=BUY, 卖出=SELL
            price: 价格
            qty: 数量
            order_type: NORMAL=普通, MARKET=市价
            env: 1=模拟 0=实盘
        """
        if not self.trade_ctx:
            return {"ret": -1, "msg": "Not logged in"}
            
        try:
            ret, data = self.trade_ctx.place_order(
                order_type=order_type,
                side=side,
                code=symbol,
                price=price,
                qty=qty,
                env=env
            )
            if ret == 0:
                return {"ret": 0, "data": data.to_dict()}
            return {"ret": ret, "msg": str(data)}
        except Exception as e:
            logger.error(f"下单失败: {e}")
            return {"ret": -1, "msg": str(e)}
    
    def get_positions(self, env: int = 1) -> List[Dict]:
        """获取持仓"""
        if not self.trade_ctx:
            return []
            
        try:
            ret, data = self.trade_ctx.get_position_list(env=env)
            if ret == 0:
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
            if ret == 0:
                return data.iloc[0].to_dict()
            return {}
        except Exception as e:
            logger.error(f"获取资金失败: {e}")
            return {}
    
    def close(self):
        """关闭连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        logger.info("连接已关闭")


# ==================== 集成到主系统 ====================
def create_futu_trader(config: dict) -> FutuTrader:
    """从配置创建交易客户端"""
    trader = FutuTrader()
    
    # 连接设置
    host = config.get("futu", {}).get("host", "127.0.0.1")
    port = config.get("futu", {}).get("port", 11111)
    conn_key = config.get("futu", {}).get("conn_key", "")
    
    trader.host = host
    trader.port = port
    
    if conn_key and trader.connect(conn_key):
        trader.login(conn_key)
    
    return trader


# ==================== 测试 ====================
if __name__ == "__main__":
    print("=== 富途交易系统 ===")
    print("需要先启动富途量化管理器")
    print("然后运行: pip install futu-api")
