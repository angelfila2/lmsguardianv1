from pydantic import BaseModel


class ModuleBase(BaseModel):
    module_id: int
    uc_id: int
    module_name: str
    teaching_period: str
    semester: str
    module_description: str
    unit_code: str


class ModuleCreate(ModuleBase):
    pass


class Module(ModuleBase):
    module_id: int

    class Config:
        orm_mode = True
