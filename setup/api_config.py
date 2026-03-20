#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 配置模块
功能: 管理 Futu API 和 Finnhub API 的配置
作者: 虾虾 🦐
"""

import json
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class APIConfig:
    """API配置管理器"""
    
    def __init__(self, config_file: str = "config/api_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "futu": {
                "host": "127.0.0.1",
                "port": 11111,
                "account": "",  # 牛牛号/手机号
                "password": ""   # 密码（加密存储）
            },
            "finnhub": {
                "api_key": ""    # Finnhub API Key
            },
            "alpha_vantage": {
                "api_key": ""    # Alpha Vantage API Key
            }
        }
    
    def _save_config(self):
        """保存配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        finnhub = bool(self.config.get("finnhub", {}).get("api_key"))
        futu = bool(self.config.get("futu", {}).get("account"))
        return finnhub or futu
    
    def get_futu_config(self) -> Dict:
        """获取富途配置"""
        return self.config.get("futu", {})
    
    def get_finnhub_key(self) -> str:
        """获取Finnhub API Key"""
        return self.config.get("finnhub", {}).get("api_key", "")
    
    def get_alpha_vantage_key(self) -> str:
        """获取Alpha Vantage API Key"""
        return self.config.get("alpha_vantage", {}).get("api_key", "")
    
    def update_futu(self, account: str, password: str = "", host: str = "127.0.0.1", port: int = 11111):
        """更新富途配置"""
        self.config["futu"] = {
            "host": host,
            "port": port,
            "account": account,
            "password": password
        }
        self._save_config()
        logger.info("富途配置已更新")
    
    def update_finnhub(self, api_key: str):
        """更新Finnhub配置"""
        self.config["finnhub"] = {"api_key": api_key}
        self._save_config()
        logger.info("Finnhub配置已更新")
    
    def update_alpha_vantage(self, api_key: str):
        """更新Alpha Vantage配置"""
        self.config["alpha_vantage"] = {"api_key": api_key}
        self._save_config()
        logger.info("Alpha Vantage配置已更新")


def setup_api_config():
    """交互式API配置"""
    print("=" * 50)
    print("API 配置向导")
    print("=" * 50)
    print()
    
    config = APIConfig()
    
    # Finnhub配置
    print("1. Finnhub API Key")
    print("   获取地址: https://finnhub.io/")
    existing_key = config.get_finnhub_key()
    if existing_key:
        print(f"   当前: {existing_key[:20]}...")
    finnhub_key = input("   输入新的API Key (直接回车跳过): ").strip()
    if finnhub_key:
        config.update_finnhub(finnhub_key)
    print()
    
    # 富途配置
    print("2. 富途 OpenD 配置")
    futu_config = config.get_futu_config()
    print(f"   当前牛牛号: {futu_config.get('account', '未设置')}")
    account = input("   输入牛牛号/手机号 (直接回车跳过): ").strip()
    if account:
        password = input("   输入密码 (直接回车跳过): ").strip()
        config.update_futu(account, password)
    print()
    
    # Alpha Vantage配置
    print("3. Alpha Vantage API Key (可选)")
    print("   获取地址: https://www.alphavantage.co/")
    av_key = input("   输入API Key (直接回车跳过): ").strip()
    if av_key:
        config.update_alpha_vantage(av_key)
    print()
    
    # 完成
    if config.is_configured():
        print("✅ 配置完成！")
    else:
        print("⚠️ 尚未配置任何API，请至少配置Finnhub")
    
    return config


if __name__ == "__main__":
    setup_api_config()
