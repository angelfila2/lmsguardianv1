from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.database import Base
from sqlalchemy.orm import relationship


class Module(Base):
    __tablename__ = "modules"

    module_id = Column(Integer, primary_key=True, index=True)
    uc_id = Column(Integer, ForeignKey("unit_coordinators.id"), nullable=False)
    module_name = Column(String, nullable=False)
    teaching_period = Column(String, nullable=False)
    semester = Column(String, nullable=False)
    module_description = Column(String, nullable=False)
    unit_code = Column(String, nullable=False)

    modules = relationship("Module", back_populates="coordinator")
