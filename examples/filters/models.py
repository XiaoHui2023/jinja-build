from pydantic import BaseModel


class Data(BaseModel):
    raw: str
    items: list[str]

    @property
    def label(self) -> str:
        """property：在模板里当变量用 {{ label }}。"""
        return self.raw.upper()

    def title(self) -> str:
        """实例方法：可作过滤器 {{ '' | title }} 或函数 {{ title() }}。"""
        return f"title:{self.raw}"

    def wrap(self, prefix: str) -> str:
        """带参数的过滤器：{{ raw | wrap('>>') }}。"""
        return f"{prefix}{self.raw}{prefix}"
