# -*- coding: utf-8 -*-
"""
smartir-quant 量化微服务主入口
技术栈: FastAPI + Uvicorn + Starlette + Pydantic
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 将项目根目录与 api 目录加入 sys.path
_current_dir = Path(__file__).resolve().parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from settings import settings
from api.routes import router as api_router

# 尝试初始化 Nacos 客户端注册服务
try:
    from nacos_client import register_service
    register_service()
except Exception:
    pass

app = FastAPI(
    title="smartir-quant 量化服务",
    description="提供宏观大类资产与行业超额动态风险预算测算及全景回测接口",
    version="1.0.0"
)

# 配置 CORS 跨域中间件，方便本地与云桌面 Vue 前端直接联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载业务路由
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False
    )
