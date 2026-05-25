from pydantic import BaseModel


class Nested(BaseModel):
    label: str


class Data(BaseModel):
    project_name: str
    output_dir: str
    file_count: int
    tags: list[str]
    nested: Nested
