from io import StringIO

from pydantic import BaseModel
from rich.console import Console
from rich.tree import Tree


class Data(BaseModel):
    title: str
    children: list[str]

    def tree_text(self) -> str:
        """用 rich.tree 生成树形文本，写入模板输出（非终端打印）。"""
        tree = Tree(self.title)
        for child in self.children:
            tree.add(child)
        buf = StringIO()
        Console(file=buf, width=80, force_terminal=True, no_color=True).print(tree)
        return buf.getvalue().rstrip("\n")
