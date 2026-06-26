# 配置变量引用

configlib 在加载配置时展开 `${…}`，展开后的 dict 再交给 `models.py` 主类。模板里用的是**解析后的字段**，不在 `.j2` 里写 `${}`。

## 绝对路径引用

```yaml
vars:
  prefix: acme
  version: 3
project_name: ${vars.prefix}-app-v${vars.version}
```

从配置根上的键取值；数字按规则转为 int。

## 引用同级字段

```yaml
paths:
  base: ${vars.prefix}_root
output_dir: ${paths.base}/out
```

后写字段可引用先解析的同级键。

## 嵌入字符串

```yaml
nested:
  label: ${project_name}-build
```

`${}` 可写在字符串中间。

## 其它写法

- `${..key}` — 相对引用
- `${env:NAME}` — 环境变量
- `${env:NAME:默认值}` — 带默认值
