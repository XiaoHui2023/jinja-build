from pydantic import BaseModel


class Data(BaseModel):
    class_prefix: str
    trees: list[dict]
