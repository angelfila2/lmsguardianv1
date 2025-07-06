from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.database.database import getDb
from app.schemas import scrapedContent as schemas
from app.crud import scrapedContent as crud

router = APIRouter(prefix="/scrapedcontents", tags=["Scraped Contents"])


@router.get("/", response_model=List[schemas.ScrapedContent])
def get_all_scraped_contents(db: Session = Depends(getDb)):
    return crud.getAll(db)


@router.post("/", response_model=schemas.ScrapedContent)
def create_scraped_content(
    item: schemas.ScrapedContentCreate, db: Session = Depends(getDb)
):
    return crud.create_scraped_content(db, item)


@router.put("/updaterisk/{link_id}")
def update_risk_info_api(
    link_id: int, score: float, category: str, db: Session = Depends(getDb)
):
    rows_updated = crud.update_risk_info(db, link_id, score, category)
    if rows_updated == 0:
        raise HTTPException(status_code=404, detail="Link not found")
    return {
        "message": "Risk info updated",
        "link_id": link_id,
        "new_score": score,
        "new_category": category,
    }


@router.get("/risks", response_model=List[schemas.HighRiskLink])
def get_high_risks(db: Session = Depends(getDb)):
    return crud.get_latest_session_high_risks(db)


@router.get("/highrisks", response_model=List[schemas.ScrapedContent])
def get_negative_risks(db: Session = Depends(getDb)):
    return crud.get_latest_session_negative_risks(db)
