from pydantic import BaseModel


class Data(BaseModel):
    emit_readme: bool
    emit_extra: bool
    project: str
