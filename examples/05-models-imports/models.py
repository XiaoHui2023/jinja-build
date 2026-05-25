from pydantic import BaseModel

from demo_lib.formats import format_title, slugify


class Data(BaseModel):
    name: str

    def display(self) -> str:
        return format_title(self.name)

    def slug(self) -> str:
        return slugify(self.name)
