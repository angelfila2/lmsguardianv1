from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HighRiskLink(BaseModel):
    url: str
    risk: str
    date: datetime
    scrapeID: int

    model_config = {"from_attributes": True}


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


class ScrapedContentCreate(BaseModel):
    module_id: int
    session_id: int
    scraped_at: Optional[datetime] = None
    url_link: str
    risk_status: Optional[str] = None
    content_location: Optional[str] = None
    is_paywall: Optional[bool] = False
    apa7: Optional[str] = None

    model_config = {"from_attributes": True}


class UnitCoordinatorOut(BaseModel):
    uc_id: int
    full_name: str
    email: str
    model_config = {"from_attributes": True}
