# jinja-build

## 演示

![输入配置、数据结构、渲染模板](images/pipeline.drawio.svg)

### config.yaml

```yaml
greeting: Hello
items:
  - name: alpha
    active: true
  - name: beta
    active: false
  - name: gamma
    active: true
```

### models.py

```python
from pydantic import BaseModel


class Item(BaseModel):
    name: str
    active: bool = True


class Data(BaseModel):
    greeting: str
    items: list[Item]

    @property
    def headline(self) -> str:
        return self.greeting.upper()

    def tag(self, text: str) -> str:
        return f"<<{text}>>"
```

### report.j2

```jinja2
{{ headline }}

{% for item in items %}
{% if item.active %}
* {{ item.name | upper }} {{ item.name | tag }}
{% else %}
# skip {{ item.name }}
{% endif %}
{% endfor %}
```

### 生成结果

```text
HELLO

* ALPHA <<alpha>>
# skip beta
* GAMMA <<gamma>>
```

## 命令行参数

| 长参数 | 短参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `--template` | `-t` | 目录 | ✓ | | 模板目录。 |
| `--output` | `-o` | 路径 | ✓ | | 渲染结果写出路径。 |
| `--input` | `-i` | 文件路径 | | | 单次构建的输入配置；与 `--batch` 互斥。 |
| `--batch` | `-b` | 多个文件路径 | | | 多份输入配置共用模板；与 `--input` 互斥。 |
| `--models-filename` | `-mf` | 文件名 | | `models.py` | 模板目录中的数据结构文件名。 |
| `--debug-input` | | 文件路径 | | | 调试文件，输入配置解析后。 |
| `--debug-models` | | 文件路径 | | | 调试文件，数据结构渲染后。 |
| `--theme` | | `auto` / `light` / `dark` / `none` | | `auto` | 颜色主题。 |

## 使用

### 单个输入

`-i` 与 `-b` 互斥。省略 `-i` 时用空配置实例化 `models.py` 的最后一个顶层类。`-o` 为渲染结果的写出路径，可以是文件或目录。

```makefile
TOOL       := /path/to/tool                 # 可执行文件或脚本
TEMPLATE   := /path/to/templates/chip       # 模板族目录
OUTPUT     := /path/to/out/generated        # 渲染结果写出路径（文件或目录）
INPUT      := /path/to/in/chip.yaml         # 单次构建用的配置文件
# MODELS_FILENAME := custom_models.py       # 模板目录内非默认的数据结构文件名
# DEBUG_INPUT  := /path/to/out/input.json   # 对照配置解析中间结果
# DEBUG_MODELS := /path/to/out/models.json  # 对照 models 实例化中间结果
# THEME := dark                             # 终端错误提示配色

.PHONY: render
render:
	$(TOOL) -t $(TEMPLATE) -o $(OUTPUT) -i $(INPUT)
#	-mf $(MODELS_FILENAME) --debug-input $(DEBUG_INPUT) \
#	--debug-models $(DEBUG_MODELS) --theme $(THEME)
```

### 批量输入

多份输入配置文件共用同一套模板。`-o` 为输出根目录；每份输入在其下各占以配置文件名（不含扩展名）命名的子目录。

```makefile
TOOL       := /path/to/tool                 # 可执行文件或脚本
TEMPLATE   := /path/to/templates/chip       # 模板族目录
OUTPUT     := /path/to/out/batch            # 批量构建的输出根目录
BATCH     += /path/to/in/scene_a.yaml      # 批量构建的第一份配置
BATCH     += /path/to/in/scene_b.yaml      # 批量构建的另一份配置
# MODELS_FILENAME := custom_models.py       # 模板目录内非默认的数据结构文件名
# DEBUG_INPUT  := /path/to/out/input.json   # 对照配置解析中间结果
# DEBUG_MODELS := /path/to/out/models.json  # 对照 models 实例化中间结果
# THEME := dark                             # 终端错误提示配色

.PHONY: render
render:
	$(TOOL) -t $(TEMPLATE) -o $(OUTPUT) -b $(BATCH)
#	-mf $(MODELS_FILENAME) --debug-input $(DEBUG_INPUT) \
#	--debug-models $(DEBUG_MODELS) --theme $(THEME)
```
