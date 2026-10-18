# -*- coding: utf-8 -*-
"""
Nacos 微服务注册与心跳保持模块 (支持内网微服务体系)
当内网配置了 NACOS_SERVER_ADDR 时自动注册，未配置时安全跳过
"""
import logging
from settings import settings

logger = logging.getLogger("smartir-quant.nacos")


def register_service():
    if not settings.NACOS_SERVER_ADDR:
        logger.info("未配置 NACOS_SERVER_ADDR，跳过 Nacos 注册中心服务注册")
        return

    try:
        import nacos
        client = nacos.NacosClient(
            settings.NACOS_SERVER_ADDR,
            namespace=settings.NACOS_NAMESPACE
        )
        client.add_naming_instance(
            service_name=settings.APP_NAME,
            ip=settings.APP_HOST if settings.APP_HOST != "0.0.0.0" else "127.0.0.1",
            port=settings.APP_PORT,
            group_name=settings.NACOS_GROUP
        )
        logger.info(f"成功将服务 {settings.APP_NAME} 注册到 Nacos: {settings.NACOS_SERVER_ADDR}")
    except ImportError:
        logger.warning("未检测到 nacos-sdk-python 依赖，如需接入 Nacos 注册中心请执行 pip install nacos-sdk-python")
    except Exception as e:
        logger.warning(f"注册到 Nacos 服务中心失败 ({e})，继续以独立服务运行")
