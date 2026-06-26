# 第三方库 rich

`rich` 等已安装依赖写在 `models.py`，不要写在 `.j2` 里。模板目录下勿放名为 `rich.py` 或 `rich/` 的文件，以免挡住真正的包。

## 导入与导出文本

```python
from io import StringIO
from rich.console import Console
from rich.tree import Tree

def tree_text(self) -> str:
    tree = Tree(self.title)
    for child in self.children:
        tree.add(child)
    buf = StringIO()
    Console(file=buf, width=80, force_terminal=True, no_color=True).print(tree)
    return buf.getvalue().rstrip("\n")
```

`rich` 默认打印到终端；写入生成文件需导出到字符串。

## 模板

```jinja
{{ tree_text() }}
```

方法返回值进入模板输出。
