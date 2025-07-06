from pydantic import BaseModel
from typing import Optional
from datetime import datetime




class ModuleId(BaseModel):
    module_id: int

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    module_id: int
    uc_id: int
    module_name: str
    teaching_period: str
    semester: str
    module_description: str
    unit_code: str

    model_config = {"from_attributes": True}


class ScraperSessionCreate(BaseModel):
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    completion_status: Optional[str] = None
    error_log: Optional[str] = None


class ScraperSessionResponse(ScraperSessionCreate):
    session_id: int
    model_config = {"from_attributes": True}


