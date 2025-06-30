from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from .database import SessionLocal
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


@router.put("/updaterisk/{link_id}")
def update_risk_info_api(
    link_id: int, score: float, category: str, db: Session = Depends(get_db)
):
    query = text(
        """
        UPDATE scraped_contents
        SET risk_score = :score,
            risk_category = :category
        WHERE scraped_id = :id
        """
    )

    result = db.execute(query, {"score": score, "category": category, "id": link_id})

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Link not found")

    db.commit()
    return {
        "message": "Risk info updated",
        "link_id": link_id,
        "new_score": score,
        "new_category": category,
    }


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


@router.post("/scraped-contents", response_model=schemas.ScrapedContentCreate)
def create_scraped_content(
    item: schemas.ScrapedContentCreate, db: Session = Depends(get_db)
):
    data = item.dict()
    if not data.get("scraped_at"):
        data["scraped_at"] = datetime.utcnow()

    content = models.ScrapedContent(**data)
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


from sqlalchemy import text


@router.get("/risks", response_model=List[schemas.HighRiskLink])
def get_high_risk_links(db: Session = Depends(get_db)):
    query = text(
        """
        SELECT scraped_id AS "scrapeID", url_link AS url, risk_score AS score, risk_category AS category, scraped_at AS date
        FROM scraped_contents
        WHERE session_id = (
            SELECT MAX(session_id) FROM scraper_sessions
        )
    """
    )
    result = db.execute(query).mappings().all()
    return list(result)


@router.get("/highrisks", response_model=List[schemas.ScrapedContentCreate])
def get_high_risk_links(db: Session = Depends(get_db)):
    query = text(
        """
        SELECT *
        FROM scraped_contents
        WHERE session_id = (
            SELECT MAX(session_id) FROM scraper_sessions
        )
        AND risk_score < 0 
        """
    )

    result = db.execute(query).mappings().all()
    return list(result)
