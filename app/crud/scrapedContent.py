from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.schemas.scrapedContent import ScrapedContentCreate


def create_scraped_content(db: Session, item: ScrapedContentCreate):
    data = item.dict()
    if not data.get("scraped_at"):
        data["scraped_at"] = datetime.utcnow()

    sql = text(
        """
        INSERT INTO scraped_contents (
            module_id, session_id, scraped_at, url_link,
            risk_category, risk_score, content_location,
            is_paywall, apa7
        )
        VALUES (
            :module_id, :session_id, :scraped_at, :url_link,
            :risk_category, :risk_score, :content_location,
            :is_paywall, :apa7
        )
        RETURNING *
    """
    )

    result = db.execute(sql, data).mappings()
    db.commit()
    return dict(result.fetchone())


def update_risk_info(db: Session, link_id: int, score: float, category: str):
    sql = text(
        """
        UPDATE scraped_contents
        SET risk_score = :score,
            risk_category = :category
        WHERE scraped_id = :id
    """
    )

    result = db.execute(sql, {"score": score, "category": category, "id": link_id})
    db.commit()
    return result.rowcount


def get_latest_session_high_risks(db: Session):
    sql = text(
        """
        SELECT scraped_id AS "scrapeID", url_link AS url,
               risk_score AS score, risk_category AS category,
               scraped_at AS date
        FROM scraped_contents
        WHERE session_id = (SELECT MAX(session_id) FROM scraper_sessions)
    """
    )
    result = db.execute(sql).mappings().all()
    return list(result)


def get_latest_session_negative_risks(db: Session):
    sql = text(
        """
        SELECT *
        FROM scraped_contents
        WHERE session_id = (SELECT MAX(session_id) FROM scraper_sessions)
        AND risk_score < 0
    """
    )
    result = db.execute(sql).mappings().all()
    return list(result)


def getAll(db: Session):
    sql = text("SELECT * FROM scraped_contents")
    result = db.execute(sql).mappings().all()
    return [dict(row) for row in result]


def getById(db: Session, coordinatorId: int):
    sql = text("SELECT uc_id, full_name,email  FROM unit_coordinators WHERE id = :id")
    result = db.execute(sql, {"id": coordinatorId}).fetchone()
    return dict(result) if result else None
