# 如何编写 models.py

每个模板目录（或单文件模板所在目录）里放一份 **`models.py`**（可用 `-mf` 改成别的文件名）。  
jinja-build 读取输入配置后，用其中的类型把配置变成模板可用的数据对象。

本文说明推荐写法，以及如何用 **Pydantic** 在配置写错时**立刻失败**（`ValidationError`），而不是悄悄忽略或带病渲染。

## 在构建流程中的位置

```text
config.yaml（等）  →  configlib 载入为 dict  →  主类(**dict)  →  模板 {{ 字段 }}
```

- 配置文件里的 `${…}` 引用由 **configlib** 在载入阶段解析，见 [examples/06-config-variables](../examples/06-config-variables/README.md)。
- **校验发生在 `主类(**dict)`**，早于任何 `.j2` 渲染；失败时不会写出产物文件。

## 文件里要有哪些 class

`models.py` 里可以定义多个 class，规则如下：

| 顺序 | 作用 |
| --- | --- |
| **最后一个** `class` | **主数据类**：用输入配置实例化，字段与 `@property` 供模板 `{{ name }}` 使用 |
| **前面的** `class` | 注册为模板**全局类型名**（如 `Item`），可在模板里引用类型本身；也常作嵌套模型 |

示范见 [examples/01-jinja-basics/models.py](../examples/01-jinja-basics/models.py)（`Item` + `Data`）。

主类上的**公开实例方法**还可同时作为管道过滤器和 `{{ method() }}` 调用，见 [examples/02-filters](../examples/02-filters/README.md)。

同目录的 `helper.py`、`demo_lib/` 等可在 `models.py` 里 `import`；加载时会把 `models.py` 所在目录临时加入模块搜索路径。

## 为何推荐 Pydantic

| 方式 | 配置多写了键 | 键名拼错 | 类型不对（如 `"3"` 当 int） | 缺必填字段 |
| --- | --- | --- | --- | --- |
| **Pydantic + 严格配置** | 可报错 | 可报错 | 可报错（`strict=True`） | 报错 |
| 普通 `class` + `__init__` | 常忽略 | 常忽略 | 常忽略 | 仅当你手写检查 |
| **dataclass** | 常忽略 | 常忽略 | 常忽略 | 仅当你手写检查 |

项目已依赖 Pydantic；结构说明工具（`jinja-build-schema`）也对 Pydantic / dataclass 生成字段表。  
**若希望配置笔误在 CI 里就拦住，请用 Pydantic 并按下文打开严格项。**

## 严格校验：两套开关

### 1. 禁止未声明字段（`extra='forbid'`）

Pydantic v2 **默认**会**忽略**配置里多出来的键。  
键名拼错（如 `project_nmae`）时，若模型里没有这个字段，默认行为相当于**静默丢弃**，模板里可能变成空值或触发 `StrictUndefined`，难以一眼看出是配置错误。

设置 **`extra='forbid'`** 后，多出的键（含拼写错误的键名）会在实例化时报 `ValidationError`。

### 2. 禁止宽松类型转换（`strict=True`）

默认情况下，部分标量会把字符串自动转成数字（如 `"3"` → `3`）。  
若希望类型必须与注解一致（配置里是字符串就报错），设置 **`strict=True`**。

### 推荐：统一基类

在 `models.py` 顶部定义一次，所有模型继承：

```python
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """输入配置与嵌套结构共用：未知键、类型不符均失败。"""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )


class Item(StrictModel):
    name: str
    qty: int = 1


class Data(StrictModel):
    project_name: str
    items: list[Item]
```

**嵌套模型**（如 `Item`、`Nested`）也要继承同一套 `StrictModel`（或同样写上 `model_config`）。  
否则外层虽禁止多余键，内层 dict 仍可能按子模型自己的规则放宽。

### 单文件内完整示例

```python
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Nested(StrictModel):
    label: str


class Data(StrictModel):
    project_name: str
    file_count: int
    nested: Nested
    tags: list[str] = Field(default_factory=list)
```

对应 `config.yaml`：

```yaml
project_name: demo
file_count: 3
nested:
  label: build-a
tags:
  - a
  - b
```

会失败的情况举例：

| 配置问题 | 典型报错原因 |
| --- | --- |
| `project_nmae: demo` | 未声明字段 `project_nmae`（`extra_forbidden`） |
| `file_count: "3"` | `strict=True` 时不接受字符串形式的整数 |
| 删掉 `nested` | 缺少必填字段 `nested` |
| `nested: { label: x, typo: 1 }` | 嵌套对象含未声明字段 `typo` |

命令行上表现为 Python 异常 **`pydantic.ValidationError`**，构建中止；修正配置或模型后重新运行即可。

## 常用补充设置（按需）

在 `ConfigDict` 或 `Field` 上按仓库约定选用，例如：

| 设置 | 作用 |
| --- | --- |
| `str_strip_whitespace=True` | 字符串去掉首尾空白再校验 |
| `validate_assignment=True` | 实例创建后改字段也重新校验 |
| `frozen=True` | 实例只读，防止渲染前被改掉 |
| `Field(min_length=1)` / `ge=0` | 约束字符串长度、数值范围 |

字段别名（YAML 用 `snake_case`、模型用别名）需同时考虑 `Field(alias=...)` 与 `populate_by_name=True`（或 `validation_alias` / `serialization_alias`），否则配置键名与模型字段对不上时也会校验失败。  
模板侧序列化使用 **`model_dump(by_alias=True)`**，别名会影响 `{{ }}` 里出现的键名。

## 与 dataclass、普通 class 并存时

- 项目**支持** dataclass 和普通 class 作为最后一个类；`to_dict` 会递归展开 dataclass / `@property`。
- 它们**不会**自动具备 `extra='forbid'`；拼错键名时往往只是没赋到属性上。
- 若已引入 Pydantic，建议**主数据类与所有嵌套结构**都使用 `StrictModel`，避免一半严格、一半宽松。

## 调试建议

1. 本地用故意写错的 `config.yaml` 跑一遍 `jinja-build`，确认出现 `ValidationError` 且错误列表指向具体字段。
2. 把 `StrictModel` 放在团队模板仓库的公共模块里复用，避免每个项目各写一份 `model_config`。
3. 字段增多后，可配合 **`jinja-build-schema`** 生成 Markdown 字段表，与 `models.py` 对照（见 `schema/README.md`）。

## 相关示范

| 目录 | 内容 |
| --- | --- |
| [01-jinja-basics](../examples/01-jinja-basics/) | 多 class、嵌套列表 |
| [02-filters](../examples/02-filters/) | 方法作过滤器、`@property` |
| [05-models-imports](../examples/05-models-imports/) | 同目录 Python 包复用 |
| [06-config-variables](../examples/06-config-variables/) | `${…}` 与 YAML 组合 |

生成命令见仓库根目录 `example.bat` / `example.sh` 与 [examples/README.md](../examples/README.md)。
