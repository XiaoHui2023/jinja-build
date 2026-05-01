from dataclasses import dataclass


MAX_CONFIG_FILE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class UploadedFile:
    """请求里上传的一份输入配置。"""

    filename: str
    content: bytes


@dataclass(frozen=True)
class DownloadFile:
    """一次渲染后返回给调用方的文件内容。"""

    filename: str
    content_type: str
    content: bytes
