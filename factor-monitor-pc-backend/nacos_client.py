# -*- coding: utf-8 -*-
"""
Nacos 微服务注册与心跳保持模块 (直接调用 Nacos HTTP Open API v1)
兼容 Nacos 1.x / 2.x，无需安装 nacos-sdk-python，仅依赖 requests
"""
import json
import logging
import socket
import threading
import time

import requests

from settings import settings

logger = logging.getLogger("smartir-quant.nacos")

# 心跳间隔（秒），Nacos 默认实例超时为 15s，心跳建议 5s
_HEARTBEAT_INTERVAL = 5

# 后台心跳线程控制标志
_stop_event = threading.Event()
_heartbeat_thread: threading.Thread | None = None


def _get_local_ip() -> str:
    """获取本机出口 IP（非 0.0.0.0 时直接使用配置值）"""
    if settings.APP_HOST not in ("0.0.0.0", ""):
        return settings.APP_HOST
    try:
        # 通过连接 Nacos 服务端获取本机出口 IP
        host = settings.NACOS_SERVER_ADDR.split(":")[0]
        with socket.create_connection((host, 8848), timeout=2) as s:
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def _build_base_url() -> str:
    addr = settings.NACOS_SERVER_ADDR
    if not addr.startswith("http"):
        addr = "http://" + addr
    return addr.rstrip("/") + "/nacos/v1/ns"


def _register(ip: str, port: int) -> bool:
    """向 Nacos 注册服务实例"""
    url = _build_base_url() + "/instance"
    params = {
        "serviceName": settings.APP_NAME,
        "groupName": settings.NACOS_GROUP,
        "ip": ip,
        "port": port,
        "ephemeral": "true",
        "weight": 1.0,
        "enabled": "true",
        "healthy": "true",
    }
    if settings.NACOS_NAMESPACE:
        params["namespaceId"] = settings.NACOS_NAMESPACE
    try:
        resp = requests.post(url, params=params, timeout=5)
        return resp.status_code == 200 and resp.text.strip() == "ok"
    except Exception as e:
        logger.warning(f"注册请求失败: {e}")
        return False


def _send_heartbeat(ip: str, port: int):
    """向 Nacos 发送一次心跳"""
    url = _build_base_url() + "/instance/beat"
    beat_info = {
        "serviceName": settings.APP_NAME,
        "groupName": settings.NACOS_GROUP,
        "ip": ip,
        "port": port,
    }
    params = {
        "serviceName": settings.APP_NAME,
        "groupName": settings.NACOS_GROUP,
        "beat": json.dumps(beat_info),
    }
    if settings.NACOS_NAMESPACE:
        params["namespaceId"] = settings.NACOS_NAMESPACE
    try:
        requests.put(url, params=params, timeout=5)
    except Exception as e:
        logger.debug(f"心跳发送失败: {e}")


def _heartbeat_loop(ip: str, port: int):
    """后台心跳线程，每 5 秒发送一次心跳"""
    while not _stop_event.is_set():
        _send_heartbeat(ip, port)
        _stop_event.wait(_HEARTBEAT_INTERVAL)


def _deregister(ip: str, port: int):
    """从 Nacos 注销服务实例"""
    url = _build_base_url() + "/instance"
    params = {
        "serviceName": settings.APP_NAME,
        "groupName": settings.NACOS_GROUP,
        "ip": ip,
        "port": port,
    }
    if settings.NACOS_NAMESPACE:
        params["namespaceId"] = settings.NACOS_NAMESPACE
    try:
        requests.delete(url, params=params, timeout=5)
    except Exception as e:
        logger.debug(f"注销请求失败: {e}")


# ──────────────────────────────────────────────
# 对外接口：供 main.py lifespan 调用
# ──────────────────────────────────────────────

_registered_ip: str = "127.0.0.1"
_registered_port: int = 8000


def register_service():
    """启动时向 Nacos 注册当前服务实例，并开启后台心跳线程"""
    global _heartbeat_thread, _registered_ip, _registered_port

    if not settings.NACOS_SERVER_ADDR:
        logger.info("未配置 NACOS_SERVER_ADDR，跳过 Nacos 注册中心服务注册")
        return

    _registered_ip = _get_local_ip()
    _registered_port = settings.APP_PORT

    if _register(_registered_ip, _registered_port):
        logger.info(
            f"成功将服务 {settings.APP_NAME} ({_registered_ip}:{_registered_port}) "
            f"注册到 Nacos: {settings.NACOS_SERVER_ADDR}"
        )
        # 启动后台心跳线程
        _stop_event.clear()
        _heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(_registered_ip, _registered_port),
            daemon=True,
            name="nacos-heartbeat",
        )
        _heartbeat_thread.start()
        logger.info("Nacos 心跳线程已启动（每 5 秒保活一次）")
    else:
        logger.warning(
            f"注册到 Nacos 服务中心失败，继续以独立服务运行。"
            f"请检查 Nacos 地址：{settings.NACOS_SERVER_ADDR}"
        )


def deregister_service():
    """关闭时停止心跳并从 Nacos 注销服务实例"""
    global _heartbeat_thread

    # 停止心跳线程
    _stop_event.set()
    if _heartbeat_thread and _heartbeat_thread.is_alive():
        _heartbeat_thread.join(timeout=3)
        _heartbeat_thread = None

    if not settings.NACOS_SERVER_ADDR:
        return

    _deregister(_registered_ip, _registered_port)
    logger.info(f"已将服务 {settings.APP_NAME} 从 Nacos 注销")
