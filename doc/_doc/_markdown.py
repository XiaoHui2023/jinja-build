from pathlib import Path

from .schema import ClassSchema


def render_markdown(repo_name: str, schemas: list[ClassSchema]) -> str:
    """把数据结构说明渲染成 Markdown。"""
    lines = [
        f"# {repo_name} 数据结构",
        "",
        "这份文档由仓库里的数据结构文件生成，用来快速了解输入数据长什么样。",
        "",
    ]
    if not schemas:
        lines.extend([
            "没有发现可展开的数据结构。",
            "",
        ])
        return "\n".join(lines)

    for schema in schemas:
        lines.extend(_render_class(schema))
    return "\n".join(lines).rstrip() + "\n"


def repo_display_name(relative_path: Path, root: Path) -> str:
    """生成文档标题里使用的仓库名称。"""
    if str(relative_path) == ".":
        return root.name
    return relative_path.as_posix()


def _render_class(schema: ClassSchema) -> list[str]:
    """渲染单个数据结构类。"""
    lines = [
        f"## {schema.name}",
        "",
        f"类型：{schema.kind}",
        "",
    ]
    description = _clean_doc(schema.description)
    if description:
        lines.extend([description, ""])

    if not schema.fields:
        lines.extend(["没有声明字段。", ""])
        return lines

    lines.extend([
        "| 字段 | 类型 | 必填 | 默认 | 说明 |",
        "| --- | --- | --- | --- | --- |",
    ])
    for field in schema.fields:
        lines.append(
            "| "
            + " | ".join([
                _cell(field.name),
                _cell(field.type),
                "是" if field.required else "否",
                _cell(field.default or ""),
                _cell(field.description or ""),
            ])
            + " |"
        )
    lines.append("")
    return lines


def _clean_doc(value: str | None) -> str:
    """清理类型说明里的缩进和空行。"""
    if not value:
        return ""
    lines = [line.strip() for line in value.strip().splitlines()]
    return " ".join(line for line in lines if line)


def _cell(value: str) -> str:
    """转义 Markdown 表格单元格。"""
    return value.replace("|", "\\|").replace("\n", " ")
