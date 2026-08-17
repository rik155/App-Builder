
from pydantic import BaseModel, Field
from typing import List, Literal

class PageSpec(BaseModel):
    name: str
    route: str
    purpose: str

class FeatureSpec(BaseModel):
    name: str
    description: str

class BuildPlan(BaseModel):
    app_name: str
    app_type: str
    visual_style: str
    color_direction: str
    pages: List[PageSpec] = Field(default_factory=list)
    features: List[FeatureSpec] = Field(default_factory=list)
    data_entities: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

class GeneratedFile(BaseModel):
    path: str
    content: str

class GeneratedProject(BaseModel):
    plan: BuildPlan
    files: List[GeneratedFile]
