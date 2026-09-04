from pydantic import BaseModel
from typing import Literal

class FixerResult(BaseModel):
    status: Literal["success", "failure"]
    message: str