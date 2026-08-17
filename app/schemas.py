
from pydantic import BaseModel, Field
from typing import List, Literal

class ModuleSpec(BaseModel):
    name: str
    description: str
    priority: Literal["must","should","could"] = "must"
    enabled: bool = True

class ProductBrief(BaseModel):
    app_name: str
    app_type: str
    industry: str
    target_users: List[str] = Field(default_factory=list)
    primary_goal: str
    modules: List[ModuleSpec] = Field(default_factory=list)
    workflow: List[str] = Field(default_factory=list)
    design_direction: str = "clean en professioneel"

class GeneratedFile(BaseModel):
    path: str
    content: str

class QAResult(BaseModel):
    passed: bool
    score: int
    summary: str
