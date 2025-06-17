from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class UnitCoordinator(Base):
    __tablename__ = "unit_coordinators"

    uc_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    modules = relationship("Module", back_populates="coordinator")


class Module(Base):
    __tablename__ = "modules"

    module_id = Column(Integer, primary_key=True, index=True)
    uc_id = Column(Integer, ForeignKey("unit_coordinators.uc_id"), nullable=False)
    module_name = Column(String, nullable=False)
    teaching_period = Column(String)
    semester = Column(String)
    module_description = Column(Text)
    unit_code = Column(String)

    coordinator = relationship("UnitCoordinator", back_populates="modules")
    reports = relationship("Report", back_populates="module")
    contents = relationship("ScrapedContent", back_populates="module")


class ScraperSession(Base):
    __tablename__ = "scraper_sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    completion_status = Column(String)
    error_log = Column(Text)

    reports = relationship("Report", back_populates="session")
    contents = relationship("ScrapedContent", back_populates="session")


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("scraper_sessions.session_id"), nullable=False
    )
    module_id = Column(Integer, ForeignKey("modules.module_id"), nullable=False)
    report_type = Column(String)
    report_content = Column(Text)

    session = relationship("ScraperSession", back_populates="reports")
    module = relationship("Module", back_populates="reports")


class ScrapedContent(Base):
    __tablename__ = "scraped_contents"

    scraped_id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.module_id"), nullable=False)
    session_id = Column(
        Integer, ForeignKey("scraper_sessions.session_id"), nullable=False
    )
    scraped_at = Column(DateTime)
    url_link = Column(Text)
    risk_status = Column(String)
    content_location = Column(Text)
    is_paywall = Column(Boolean, default=False)
    apa7 = Column(Text)

    module = relationship("Module", back_populates="contents")
    session = relationship("ScraperSession", back_populates="contents")
