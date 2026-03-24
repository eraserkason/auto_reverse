from __future__ import annotations

from typing import Any


class NewAPIError(Exception):
    """NewAPI SDK 基础异常。"""


class NewAPIConfigError(NewAPIError, ValueError):
    """调用前配置不合法。"""


class NewAPIRequestError(NewAPIError):
    """请求发送阶段失败。"""


class NewAPIResponseError(NewAPIError):
    """响应协议或内容无法解析。"""


class NewAPIHTTPError(NewAPIError):
    """远端返回 HTTP 错误状态。"""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        response_body: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")
