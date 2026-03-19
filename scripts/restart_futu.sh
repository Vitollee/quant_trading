#!/bin/bash
# Futu OpenD 自动启动脚本
# 检查并重启 Futu OpenD 如果它没有运行

FUTU_PATH="/home/vito/下载/Futu_OpenD_10.0.6018_Ubuntu18.04/Futu_OpenD_10.0.6018_Ubuntu18.04"
LOG_FILE="$FUTU_PATH/futu.log"
PID_FILE="$FUTU_PATH/futu.pid"

# 检查 Futu OpenD 是否在运行
is_running() {
    pgrep -f "FutuOpenD" > /dev/null 2>&1
    return $?
}

# 启动 Futu OpenD
start_futu() {
    echo "[$(date)] 启动 Futu OpenD..."
    cd "$FUTU_PATH"
    
    # 检查是否已有进程在运行
    if pgrep -f "FutuOpenD" > /dev/null; then
        echo "[$(date)] Futu OpenD 已在运行"
        return 0
    fi
    
    # 启动（后台运行）
    nohup ./FutuOpenD > /dev/null 2>&1 &
    NEW_PID=$!
    echo $NEW_PID > "$PID_FILE"
    
    sleep 3
    
    if is_running; then
        echo "[$(date)] Futu OpenD 启动成功 (PID: $NEW_PID)"
        return 0
    else
        echo "[$(date)] Futu OpenD 启动失败"
        return 1
    fi
}

# 主程序
case "$1" in
    start)
        start_futu
        ;;
    stop)
        echo "[$(date)] 停止 Futu OpenD..."
        pkill -f "FutuOpenD"
        rm -f "$PID_FILE"
        ;;
    restart)
        echo "[$(date)] 重启 Futu OpenD..."
        pkill -f "FutuOpenD"
        sleep 2
        start_futu
        ;;
    status)
        if is_running; then
            echo "✅ Futu OpenD 正在运行"
            pgrep -f "FutuOpenD" | while read pid; do
                echo "   PID: $pid"
            done
        else
            echo "❌ Futu OpenD 未运行"
        fi
        ;;
    *)
        # 默认：检查并启动
        if is_running; then
            echo "✅ Futu OpenD 运行正常"
        else
            echo "❌ Futu OpenD 未运行，正在启动..."
            start_futu
        fi
        ;;
esac
