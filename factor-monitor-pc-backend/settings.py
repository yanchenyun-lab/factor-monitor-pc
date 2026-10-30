# -*- coding: utf-8 -*-
"""
smartir-quant 应用全局配置
"""
import os


class Settings:
    # 服务信息
    APP_NAME: str = "smartir-quant"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1")

    # smartIR Java 后端 HTTP 数据服务基础路径
    SMARTIR_API_BASE: str = os.getenv("SMARTIR_API_BASE", "http://127.0.0.1:8080")

    # Nacos 服务注册中心配置 (本地 Nacos 默认端口 18848)
    NACOS_SERVER_ADDR: str = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:18848")
    NACOS_NAMESPACE: str = os.getenv("NACOS_NAMESPACE", "")
    NACOS_GROUP: str = os.getenv("NACOS_GROUP", "DEFAULT_GROUP")
    NACOS_EPHEMERAL: bool = os.getenv("NACOS_EPHEMERAL", "true").lower() in ("true", "1")


settings = Settings()
