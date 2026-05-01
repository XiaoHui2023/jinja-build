class TemplateNotFound(Exception):
    """模板路径不存在时带上近似路径。"""

    def __init__(self, message: str, suggestion: str | None) -> None:
        """保存错误文案和建议路径。"""
        super().__init__(message)
        self.suggestion = suggestion


class RenderNoOutput(Exception):
    """模板没有生成任何可下载内容。"""


class ConfigSizeError(Exception):
    """输入配置文件大小不正常。"""
