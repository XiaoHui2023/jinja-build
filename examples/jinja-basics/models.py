from pydantic import BaseModel


class Item(BaseModel):
    name: str
    qty: int
    active: bool = True


class Data(BaseModel):
    title: str
    enabled: bool = True
    items: list[Item]
    note: str | None = None
    count: int = 3
