from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.database.database import getDb
from app.schemas import scraperSession as schema
from app.crud import scraperSession as crud

router = APIRouter(prefix="/scrapersession", tags=["Scraper Sessions"])


@router.get("/", response_model=List[schema.ScraperSession])
def get_all_sessions(db: Session = Depends(getDb)):
    return crud.get_all_sessions(db)


@router.post("/newsession", response_model=schema.ScraperSession)
def start_new_session(db: Session = Depends(getDb)):
    return crud.start_new_session(db)
