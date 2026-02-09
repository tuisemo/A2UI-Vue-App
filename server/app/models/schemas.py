from pydantic import BaseModel
from typing import Optional, List, Any

class ChatRequest(BaseModel):
    message: str

class A2UIComponent(BaseModel):
    id: str
    component: dict

class SurfaceUpdate(BaseModel):
    surfaceId: str
    components: List[A2UIComponent]

class BeginRendering(BaseModel):
    surfaceId: str
    root: str

class A2UIMessage(BaseModel):
    surfaceUpdate: Optional[SurfaceUpdate] = None
    beginRendering: Optional[BeginRendering] = None
