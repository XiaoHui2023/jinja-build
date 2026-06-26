# models.py 引用同目录模块

构建时会把 `models.py` 所在目录加入 `sys.path`，同目录 Python 包可在顶层或方法内 `import`。

## 目录布局

```text
models.py
demo_lib/
  __init__.py
  formats.py
```

## 绝对导入

```python
from demo_lib.formats import format_title, slugify

class Data(BaseModel):
    name: str

    def display(self) -> str:
        return format_title(self.name)
```

包名从模板根目录起，写 `from demo_lib.xxx import …`，不要用仓库外的已安装包名冒充本地包。

## 模板调用

```jinja
{{ display() }}
{{ name | slug }}
```

引入的函数可在方法里用；方法同样可作过滤器。
