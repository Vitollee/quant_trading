#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Futu OpenD 健康检查与自动重启
由 AI 调用检测 API 是否正常，异常时自动重启
"""

import subprocess
import time
import socket
from futu import OpenQuoteContext

FUTU_HOST = "127.0.0.1"
FUTU_PORT = 11111
FUTU_PATH = "/root/下载/Futu_OpenD_10.0.6018_Ubuntu18.04/Futu_OpenD_10.0.6018_Ubuntu18.04"


def is_port_open(host, port, timeout=2):
    """检查端口是否开放"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except:
        return False
    finally:
        sock.close()


def is_futu_running():
    """检查 Futu OpenD 进程是否在运行"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "FutuOpenD"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False


def test_futu_api():
    """测试 Futu API 是否可用"""
    try:
        ctx = OpenQuoteContext(FUTU_HOST, FUTU_PORT)
        ret, data = ctx.get_stock_quote(['HK.00700'])
        ctx.close()
        
        if ret == 0 and data is not None:
            return True, "API 正常"
        else:
            return False, f"API 错误: {ret}"
    except Exception as e:
        return False, str(e)


def restart_futu():
    """重启 Futu OpenD"""
    print("🔄 重启 Futu OpenD...")
    
    # 停止
    subprocess.run(["pkill", "-f", "FutuOpenD"], capture_output=True)
    time.sleep(2)
    
    # 启动
    try:
        subprocess.Popen(
            ["./FutuOpenD"],
            cwd=FUTU_PATH,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        
        if is_port_open(FUTU_HOST, FUTU_PORT):
            return True, "重启成功"
        else:
            return False, "重启后端口未开放"
    except Exception as e:
        return False, f"启动失败: {e}"


def health_check(auto_restart=True):
    """健康检查"""
    print("=" * 50)
    print("🔍 Futu OpenD 健康检查")
    print("=" * 50)
    
    results = {}
    
    # 1. 检查进程
    running = is_futu_running()
    print(f"📌 进程状态: {'✅ 运行中' if running else '❌ 未运行'}")
    results['process'] = running
    
    # 2. 检查端口
    port_open = is_port_open(FUTU_HOST, FUTU_PORT)
    print(f"📌 端口状态: {'✅ 开放' if port_open else '❌ 未开放'}")
    results['port'] = port_open
    
    # 3. 测试 API（仅当进程和端口都正常时）
    if running and port_open:
        api_ok, msg = test_futu_api()
        print(f"📌 API 测试: {'✅ ' + msg if api_ok else '❌ ' + msg}")
        results['api'] = api_ok
    else:
        print(f"📌 API 测试: ⏭️ 跳过（进程或端口异常）")
        results['api'] = False
    
    # 4. 自动修复
    if auto_restart and not results['api']:
        print("\n🔧 自动修复中...")
        
        if not running or not port_open:
            success, msg = restart_futu()
            if success:
                print(f"✅ {msg}")
                # 重新测试
                api_ok, msg = test_futu_api()
                print(f"📌 API 重测: {'✅ ' + msg if api_ok else '❌ ' + msg}")
                results['api'] = api_ok
            else:
                print(f"❌ {msg}")
        else:
            print("⚠️ 进程运行中但 API 异常，尝试重启...")
            success, msg = restart_futu()
            print(f"{'✅' if success else '❌'} {msg}")
    
    # 总结
    print("\n" + "=" * 50)
    if results['api']:
        print("✅ Futu OpenD 完全正常")
    else:
        print("❌ Futu OpenD 异常，需要手动检查")
    print("=" * 50)
    
    return results['api']


if __name__ == "__main__":
    health_check(auto_restart=True)
