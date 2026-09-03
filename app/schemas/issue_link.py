from typing import Literal

from pydantic import BaseModel, ConfigDict


class IssueLinkCreate(BaseModel):
    link_type_id: int
    target_key: str
    # "outward" = this issue -> target using link_type.outward_name (e.g. "blocks")
    # "inward"  = this issue <- target using link_type.inward_name (e.g. "is blocked by")
    direction: Literal["outward", "inward"] = "outward"


class IssueLinkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    link_type_id: int
    source_issue_id: int
    target_issue_id: int
    label: str
