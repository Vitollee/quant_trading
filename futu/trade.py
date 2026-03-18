#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
富途 OpenAPI 交易模块
支持港股、美股实时行情和交易

作者: 虾虾 🦐
"""

import socket
import struct
import json
import hashlib
import hmac
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FutuClient:
    """富途 OpenAPI 客户端"""
    
    # 服务器地址
    HOST = "127.0.0.1"  # 本地量化管理器地址
    PORT = 11111        # 端口
    
    def __init__(self, conn_key: str, crypto):
        """
        初始化
        
        Args:
            conn_key: 客户端连接密钥
            crypto: Crypto 对象（用于解密）
        """
        self.conn_key = conn_key
        self.crypto = crypto
        self.socket = None
        self.connected = False
        
    def connect(self) -> bool:
        """连接服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.HOST, self.PORT))
            self.connected = True
            logger.info("Connected to Futu OpenAPI")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
            
    def login(self, encrypted_pwd: str, decrypt_pwd: str) -> Dict:
        """登录"""
        if not self.connected:
            return {"ret": -1, "msg": "Not connected"}
            
        # 构建登录请求
        req = {
            "protocol": 10004,
            "msgtype": 1002,
            "seq": int(time.time()),
            "conn_key": self.conn_key,
            "password": encrypted_pwd,
            "decrypt_pwd": decrypt_pwd,
            "client_version": "5.4.120.32888",
            "client_id": 2
        }
        
        # 发送请求
        return self._send_request(req)
    
    def get_quote(self, symbol: str, market: int = 1) -> Optional[Dict]:
        """
        获取实时报价
        
        Args:
            symbol: 股票代码 (如 00700)
            market: 市场 (1=港股, 2=美股, 6=A股)
            
        Returns:
            dict: 报价数据
        """
        req = {
            "protocol": 10004,
            "msgtype": 2201,
            "seq": int(time.time()),
            "conn_key": self.conn_key,
            "stock": {
                "code": symbol,
                "market": market
            }
        }
        
        result = self._send_request(req)
        if result.get("ret") == 0:
            return result.get("data", {})
        return None
    
    def get_history_kline(self, symbol: str, market: int = 1, 
                          start_date: str = "", end_date: str = "",
                          max_count: int = 1000) -> List[Dict]:
        """
        获取历史K线
        
        Args:
            symbol: 股票代码
            market: 市场
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            max_count: 最大数量
            
        Returns:
            list: K线数据
        """
        req = {
            "protocol": 10004,
            "msgtype": 2203,
            "seq": int(time.time()),
            "conn_key": self.conn_key,
            "stock": {
                "code": symbol,
                "market": market
            },
            "kl_type": 0,      # K线类型: 0=日, 1=周, 2=月
            "start_date": start_date,
            "end_date": end_date,
            "max_count": max_count
        }
        
        result = self._send_request(req)
        if result.get("ret") == 0:
            return result.get("data", {}).get("klines", [])
        return []
    
    def place_order(self, order_type: int, side: int, symbol: str, 
                   price: float, qty: float, market: int = 1) -> Dict:
        """
        下单
        
        Args:
            order_type: 订单类型 (0=市价, 1=限价)
            side: 方向 (1=买入, 2=卖出)
            symbol: 股票代码
            price: 价格
            qty: 数量
            market: 市场
            
        Returns:
            dict: 订单结果
        """
        req = {
            "protocol": 10004,
            "msgtype": 2001,
            "seq": int(time.time()),
            "conn_key": self.conn_key,
            "order": {
                "order_type": order_type,
                "side": side,
                "code": symbol,
                "price": price,
                "qty": qty,
                "market": market,
                "env": 1  # 1=模拟, 0=实盘
            }
        }
        
        return self._send_request(req)
    
    def get_positions(self) -> List[Dict]:
        """获取持仓"""
        req = {
            "protocol": 10004,
            "msgtype": 2011,
            "seq": int(time.time()),
            "conn_key": self.conn_key,
            "env": 1  # 1=模拟
        }
        
        result = self._send_request(req)
        if result.get("ret") == 0:
            return result.get("data", {}).get("position_list", [])
        return []
    
    def get_account(self) -> Dict:
        """获取账户资金"""
        req = {
            "protocol": 10004,
            "msgtype": 2002,
            "seq": int(time.time()),
            "conn_key": self.conn_key,
            "env": 1  # 1=模拟
        }
        
        result = self._send_request(req)
        if result.get("ret") == 0:
            return result.get("data", {})
        return {}
    
    def _send_request(self, req: Dict) -> Dict:
        """发送请求"""
        if not self.connected:
            return {"ret": -1, "msg": "Not connected"}
            
        try:
            # 序列化请求
            req_str = json.dumps(req)
            req_bytes = req_str.encode('utf-8')
            
            # 添加包头
            pkg_len = len(req_bytes) + 4
            header = struct.pack("<I", pkg_len)
            
            # 发送
            self.socket.sendall(header + req_bytes)
            
            # 接收响应
            resp_header = self.socket.recv(4)
            resp_len = struct.unpack("<I", resp_header)[0]
            resp_bytes = self.socket.recv(resp_len - 4)
            
            # 解析响应
            resp = json.loads(resp_bytes.decode('utf-8'))
            return resp
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"ret": -1, "msg": str(e)}
    
    def close(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            self.connected = False


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 你的连接密钥
    CONN_KEY = "your_conn_key_here"
    
    # 创建客户端（需要 Crypto 模块）
    # from futu import Crypto
    # crypto = Crypto()
    # client = FutuClient(CONN_KEY, crypto)
    
    # 连接并登录
    # if client.connect():
    #     # 获取港股报价
    #     quote = client.get_quote("00700", market=1)
    #     print(f"腾讯: {quote}")
    
    print("需要安装富途量化接口库: pip install futu")
    print("文档: https://openapi.futusec.com/")
