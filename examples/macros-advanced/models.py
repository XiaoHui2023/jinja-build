from pydantic import BaseModel


class Data(BaseModel):
    product: str
    version: str
