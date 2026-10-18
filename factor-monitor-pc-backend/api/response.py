# -*- coding: utf-8 -*-
"""
统一 API 响应格式封装
与内网云桌面 api/response.py 保持 100% 结构一致
"""
from typing import Any, Dict, Optional


class ResponseModel:
    @staticmethod
    def success(data: Any = None, message: str = "success") -> Dict[str, Any]:
        """成功统一响应体"""
        return {
            "success": True,
            "code": 200,
            "message": message,
            "data": data
        }

    @staticmethod
    def error(message: str = "操作失败", code: int = 500, data: Any = None) -> Dict[str, Any]:
        """失败统一响应体"""
        return {
            "success": False,
            "code": code,
            "message": str(message),
            "data": data
        }
