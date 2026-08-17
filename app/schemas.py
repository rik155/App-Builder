
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

class ContextProfile(BaseModel):
    industry: str = ""
    target_users: List[str] = Field(default_factory=list)
    core_goal: str = ""
    core_workflow: List[str] = Field(default_factory=list)
    important_objects: List[str] = Field(default_factory=list)
    possible_integrations: List[str] = Field(default_factory=list)
    risks_or_constraints: List[str] = Field(default_factory=list)

class DiscoveryResult(BaseModel):
    summary: str
    detected_app_type: str
    context: ContextProfile = Field(default_factory=ContextProfile)
    suggested_features: List[FeatureSpec] = Field(default_factory=list)
    questions: List[ClarifyingQuestion] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

class ArchitectureReview(BaseModel):
    understands_industry: bool = True
    understands_users: bool = True
    understands_workflow: bool = True
    understands_screens: bool = True
    understands_data: bool = True
    understands_integrations: bool = True
    understands_visual_style: bool = True
    notes: List[str] = Field(default_factory=list)

class BuildPlan(BaseModel):
    app_name: str
    app_type: str
    visual_style: str
    color_direction: str
    pages: List[PageSpec] = Field(default_factory=list)
    features: List[FeatureSpec] = Field(default_factory=list)
    data_entities: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    architecture_review: ArchitectureReview = Field(default_factory=ArchitectureReview)

class GeneratedFile(BaseModel):
    path: str
    content: str

class GeneratedProject(BaseModel):
    plan: BuildPlan
    files: List[GeneratedFile]
