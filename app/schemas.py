
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class PageSpec(BaseModel):
    name: str
    route: str
    purpose: str

class FeatureSpec(BaseModel):
    name: str
    description: str

class ClarifyingQuestion(BaseModel):
    id: str
    question: str
    why: str = ""
    type: Literal["text","choice","boolean"] = "text"
    options: List[str] = Field(default_factory=list)
    required: bool = True
    recommended_answer: Optional[str] = None

class DiscoveryResult(BaseModel):
    summary: str
    detected_app_type: str
    suggested_features: List[FeatureSpec] = Field(default_factory=list)
    questions: List[ClarifyingQuestion] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

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
