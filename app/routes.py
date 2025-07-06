from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from .database.database import SessionLocal
from .models import Module
from . import models, schemas
from typing import List

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/modules")
def get_modules(db: Session = Depends(get_db)):
    return db.query(Module).all()




@router.get("/moduleid", response_model=List[int])
def get_all_module_ids(db: Session = Depends(get_db)):
    query = text("SELECT module_id FROM modules")
    result = db.execute(query).fetchall()
    return [row[0] for row in result]


@router.get("/unitcoordinator/{id}")
def get_unit_coordinator_by_id(id: int, db: Session = Depends(get_db)):
    query = text("SELECT * FROM unit_coordinators WHERE uc_id = :id LIMIT 1")
    result = db.execute(query, {"id": id}).fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail="Unit Coordinator not found")

    return dict(result._mapping)  # ← this is key for SQLAlchemy 1.4+


@router.get("/module/{id}")
def getModuleInfo(id: int, db: Session = Depends(get_db)):
    query = text("SELECT * FROM modules WHERE module_id = :id LIMIT 1")
    result = db.execute(query, {"id": id}).fetchone()

    if result is None:
        raise HTTPException(status_code=404, detail="Unit Coordinator not found")

    return dict(result._mapping)  # ← this is key for SQLAlchemy 1.4+


@router.post("/newsession", response_model=schemas.ScraperSessionResponse)
def create_scraper_session(
    session_data: schemas.ScraperSessionCreate, db: Session = Depends(get_db)
):
    new_session = models.ScraperSession(**session_data.dict())
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


