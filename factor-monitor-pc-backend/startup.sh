#!/bin/bash
# smartir-quant 启动脚本
echo "正在启动 smartir-quant 量化服务..."

# 设置默认环境变量
export APP_HOST=${APP_HOST:-"0.0.0.0"}
export APP_PORT=${APP_PORT:-8000}
export SMARTIR_API_BASE=${SMARTIR_API_BASE:-"http://127.0.0.1:8080"}
export NACOS_SERVER_ADDR=${NACOS_SERVER_ADDR:-"127.0.0.1:18848"}

# 如果存在虚拟环境则激活
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 启动 uvicorn 服务
python main.py
